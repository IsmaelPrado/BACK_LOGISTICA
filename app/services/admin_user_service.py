from typing import List
import pyotp
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from app.models.associations.usuario_permisos import usuario_permisos
from app.models.user import Usuario
from app.models.rol import Rol
from app.models.permiso import Permiso
from app.schemas.user import UsuarioCreateRequest, UsuarioUpdateRequest
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
        

    async def eliminar_usuario_por_nombre(self, nombre_usuario: str) -> bool:
        """
        Elimina un usuario y sus permisos asociados por su nombre de usuario.
        Retorna True si se eliminó correctamente.
        """
        # Buscar usuario por nombre
        result = await self.db.execute(
            select(Usuario).filter(Usuario.nombre_usuario == nombre_usuario.strip())
        )
        usuario = result.scalars().first()

        if not usuario:
            raise ValueError(f"No se encontró el usuario con nombre '{nombre_usuario}'")

        try:
            # 1️⃣ Eliminar asociaciones en tabla intermedia usuario_permisos
            await self.db.execute(
                delete(usuario_permisos).where(
                    usuario_permisos.c.id_usuario == usuario.id_usuario
                )
            )

            # 2️⃣ Eliminar el usuario
            await self.db.delete(usuario)

            # 3️⃣ Confirmar cambios
            await self.db.commit()
            return True

        except IntegrityError:
            await self.db.rollback()
            raise ValueError("Error al eliminar el usuario: conflicto en la base de datos.")

        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Ocurrió un error inesperado al eliminar el usuario: {str(e)}")

     # -----------------------------
    # Actualizar usuario por nombre
    # -----------------------------
    async def actualizar_usuario_por_nombre(self, data: UsuarioUpdateRequest) -> Usuario:
        """
        Actualiza los datos de un usuario (por nombre_usuario).
        """
        result = await self.db.execute(
            select(Usuario)
            .options(selectinload(Usuario.permisos))
            .filter(Usuario.nombre_usuario == data.nombre_usuario.strip())
        )
        usuario = result.scalars().first()

        if not usuario:
            raise ValueError(f"No se encontró el usuario '{data.nombre_usuario}'")

        # Actualizar campos básicos si vienen en el request
        if data.nuevo_nombre_usuario:
            usuario.nombre_usuario = data.nuevo_nombre_usuario
        if data.correo_electronico:
            usuario.correo_electronico = data.correo_electronico
        if data.contrasena:
            usuario.contrasena = hash_password(data.contrasena)
        if data.rol:
            usuario.rol = data.rol

        # Actualizar permisos (si se proporcionan)
        if data.permisos is not None:
            permisos_query = await self.db.execute(
                select(Permiso).where(Permiso.nombre.in_(data.permisos))
            )
            permisos_encontrados = permisos_query.scalars().all()

            nombres_permisos_encontrados = [p.nombre for p in permisos_encontrados]
            permisos_faltantes = set(data.permisos) - set(nombres_permisos_encontrados)
            if permisos_faltantes:
                raise ValueError(f"Los siguientes permisos no existen: {', '.join(permisos_faltantes)}")

            usuario.permisos = permisos_encontrados

        try:
            await self.db.commit()
            await self.db.refresh(usuario)
            return usuario

        except IntegrityError:
            await self.db.rollback()
            raise ValueError("El nombre de usuario o correo ya existe.")
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Error al actualizar el usuario: {str(e)}")