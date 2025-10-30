from datetime import datetime, timedelta
import secrets
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from app.models.password_resets import PasswordReset
from app.models.sesion import Sesion
from app.models.user import Usuario
from app.core.security import hash_password, hash_password_async, verify_password
from app.schemas.auth import UsuarioRequest
from pydantic import ValidationError
import re
import pyotp

from app.schemas.user import SesionPerfilResponse, UserPerfilResponse


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate_user(self, username: str, password: str) -> Usuario | None:
        result = await self.db.execute(
            select(Usuario).filter(Usuario.nombre_usuario == username)
        )
        user: Usuario | None = result.scalars().first()

        if not user:
            raise ValueError("Usuario no existe")
        if not verify_password(password, user.contrasena):
            raise ValueError("Contraseña incorrecta")
        return user
    
    # async def update_geolocation(self, user: Usuario, lat: float | None, lon: float | None) -> None:
    #     """Guarda latitud y longitud en el usuario si existen valores"""
    #     if lat is not None and lon is not None:
    #         user.latitud = lat
    #         user.longitud = lon
    #         self.db.add(user)
    #         await self.db.commit()

    # Crear usuario
    async def create_user(self, user_data: UsuarioRequest) -> Usuario:
            # ------------------------
            # Validaciones básicas
            # ------------------------
            if not user_data.nombre_usuario or len(user_data.nombre_usuario.strip()) < 3:
                raise ValueError("El nombre de usuario debe tener al menos 3 caracteres.")

            if not user_data.contrasena or not user_data.confirmar_contrasena:
                raise ValueError("La contraseña y su confirmación no pueden estar vacías.")

            if user_data.contrasena != user_data.confirmar_contrasena:
                raise ValueError("Las contraseñas no coinciden.")

            if not user_data.rol or not user_data.rol.strip():
                raise ValueError("El rol no puede estar vacío.")

            password_pattern = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).+$')
            if not password_pattern.match(user_data.contrasena):
                raise ValueError(
                    "La contraseña debe contener mayúscula, minúscula, número y carácter especial."
                )

            # ------------------------
            # Hash de contraseña async
            # ------------------------
            hashed_password = await hash_password_async(user_data.contrasena)

            # ------------------------
            # Crear usuario
            # ------------------------
            nuevo = Usuario(
                nombre_usuario=user_data.nombre_usuario.strip(),
                correo_electronico=user_data.correo_electronico.strip(),
                contrasena=hashed_password,
                rol=user_data.rol.strip(),
                secret_2fa=pyotp.random_base32()
            )

            # ------------------------
            # Insertar con commit seguro
            # ------------------------
            async with self.db.begin():  # maneja commit/rollback automáticamente
                self.db.add(nuevo)
                try:
                    await self.db.flush()  # opcional si necesitas ID
                except IntegrityError as e:
                    # Detectar duplicados por unique constraint
                    if "nombre_usuario" in str(e.orig):
                        raise ValueError("El nombre de usuario ya está en uso")
                    elif "correo_electronico" in str(e.orig):
                        raise ValueError("El correo electrónico ya está registrado")
                    else:
                        raise ValueError("No se pudo crear el usuario (conflicto en la base de datos)")

            # Refrescar para obtener ID generado
            await self.db.refresh(nuevo)
            return nuevo


    async def get_user_by_email(self, email: str) -> Usuario | None:
        result = await self.db.execute(
            select(Usuario).filter(Usuario.correo_electronico == email)
        )
        return result.scalars().first()

    async def get_user_by_username(self, username: str) -> Usuario | None:
        result = await self.db.execute(
            select(Usuario).filter(Usuario.nombre_usuario == username)
        )
        return result.scalars().first()
    
    async def get_user_by_id(self, user_id: int) -> Usuario | None:
        result = await self.db.execute(
            select(Usuario).filter(Usuario.id_usuario == user_id)
        )
        return result.scalars().first()

    async def create_password_reset(self, user: Usuario, expire_minutes: int = 15) -> PasswordReset | None:
        """
        Genera un enlace/token o OTP de recuperación de contraseña.
        """

        # Limpiar resets previos
        await self.db.execute(
            delete(PasswordReset).where(PasswordReset.user_id == user.id_usuario)
        )
        
        # Generar token seguro
        token = secrets.token_urlsafe(32)
        expire_time = datetime.utcnow() + timedelta(minutes=expire_minutes)

        reset = PasswordReset(
            user_id=user.id_usuario,
            reset_token=token,
            expires_at=expire_time
        )
        self.db.add(reset)
        await self.db.commit()
        await self.db.refresh(reset)

        return reset

    async def verify_password_reset(self, token: str) -> PasswordReset | None:
        result = await self.db.execute(
            select(PasswordReset).filter(PasswordReset.reset_token == token)
        )
        reset: PasswordReset | None = result.scalars().first()
        if not reset:
            return None
        if reset.expires_at < datetime.utcnow():
            return None
        return reset
    
    async def update_password(self, user: Usuario, new_password: str) -> None:
         # Validar fuerza de la contraseña
        pattern = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).+$')
        if not pattern.match(new_password):
            raise ValueError(
                "La contraseña debe contener mayúscula, minúscula, número y carácter especial."
            )
        user.contrasena = hash_password(new_password)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def obtener_perfil_usuario(self, token: str) -> UserPerfilResponse:
        """
        Obtiene la información del usuario y su sesión activa a partir del token de sesión (no JWT).
        """

        # Buscar sesión activa con el token
        sesion_result = await self.db.execute(
            select(Sesion)
            .where(Sesion.token == token)
            .where(Sesion.estado == True)
        )
        sesion = sesion_result.scalar_one_or_none()

        if not sesion:
            raise ValueError("Sesión no encontrada o expirada.")

        # Buscar usuario asociado
        usuario_result = await self.db.execute(
            select(Usuario).where(Usuario.id_usuario == sesion.id_usuario)
        )
        usuario = usuario_result.scalar_one_or_none()

        if not usuario:
            raise ValueError("Usuario no encontrado para la sesión actual.")

        # Construir respuesta
        return UserPerfilResponse(
            id_usuario=usuario.id_usuario,
            nombre_usuario=usuario.nombre_usuario,
            correo_electronico=usuario.correo_electronico,
            rol=usuario.rol,
            fecha_creacion=usuario.fecha_creacion,
            sesion_actual=SesionPerfilResponse.from_orm(sesion)
        )