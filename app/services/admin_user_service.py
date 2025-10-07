from typing import List
import pyotp
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from app.models.user import Usuario
from app.models.rol import Rol
from app.models.permiso import Permiso
from app.schemas.user import UsuarioCreateRequest
from app.core.security import hash_password

class AdminUserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # -----------------------------
    # Crear usuario (solo admins)
    # -----------------------------
    async def crear_usuario(self, usuario_data: UsuarioCreateRequest) -> Usuario:
        nuevo_usuario = Usuario(
            nombre_usuario=usuario_data.nombre_usuario,
            correo_electronico=usuario_data.correo_electronico,
            contrasena=hash_password(usuario_data.contrasena),
            rol=usuario_data.rol or "usuario",
            secret_2fa=pyotp.random_base32()
        )

        # Asignar permisos si se proporcionan
        if usuario_data.permisos:
            permisos_query = await self.db.execute(
                select(Permiso).where(Permiso.nombre.in_(usuario_data.permisos))
            )
            permisos_encontrados = permisos_query.scalars().all()

            # Validar que todos los permisos existen
            nombres_permisos_encontrados = [p.nombre for p in permisos_encontrados]
            permisos_faltantes = set(usuario_data.permisos) - set(nombres_permisos_encontrados)
            if permisos_faltantes:
                raise ValueError(f"Los siguientes permisos no existen: {', '.join(permisos_faltantes)}")

            nuevo_usuario.permisos = permisos_encontrados

        self.db.add(nuevo_usuario)
        try:
            await self.db.commit()
            # Refresh con selectinload para cargar permisos sin lazy-load
            await self.db.refresh(nuevo_usuario)
            # Recargar usuario con permisos usando eager loading
            usuario_recargado = (await self.db.execute(
                select(Usuario)
                .options(selectinload(Usuario.permisos))
                .filter(Usuario.id_usuario == nuevo_usuario.id_usuario)
            )).scalars().first()
            return usuario_recargado
        except IntegrityError:
            await self.db.rollback()
            raise ValueError("El nombre de usuario o correo ya existe")
