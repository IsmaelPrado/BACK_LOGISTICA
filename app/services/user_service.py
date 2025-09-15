from datetime import datetime, timedelta
import secrets
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from app.models.password_resets import PasswordReset
from app.models.user import Usuario
from app.core.security import hash_password, verify_password
from app.schemas.auth import UsuarioRequest
import re


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

    async def create_user(self, user_data: UsuarioRequest) -> Usuario:
        # Validar coincidencia de contraseñas
        if user_data.contrasena != user_data.confirmar_contrasena:
            raise ValueError("Las contraseñas no coinciden.")

        # Validar fuerza de la contraseña
        pattern = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).+$')
        if not pattern.match(user_data.contrasena):
            raise ValueError(
                "La contraseña debe contener mayúscula, minúscula, número y carácter especial."
            )

        # Validar correo
        email_pattern = re.compile(r'^[^@]+@[^@]+\.[^@]+$')
        if not email_pattern.match(user_data.correo_electronico):
            raise ValueError("El correo electrónico no es válido.")

        # Validar duplicados
        result = await self.db.execute(
            select(Usuario).filter(Usuario.nombre_usuario == user_data.nombre_usuario)
        )
        if result.scalars().first():
            raise ValueError("El nombre de usuario ya está en uso.")

        result = await self.db.execute(
            select(Usuario).filter(Usuario.correo_electronico == user_data.correo_electronico)
        )
        if result.scalars().first():
            raise ValueError("El correo electrónico ya está registrado.")

        # Crear usuario
        nuevo = Usuario(
            nombre_usuario=user_data.nombre_usuario,
            correo_electronico=user_data.correo_electronico,
            contrasena=hash_password(user_data.contrasena),
            rol=user_data.rol
        )
        self.db.add(nuevo)

        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise ValueError("No se pudo crear el usuario (conflicto en la base de datos).")

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
        