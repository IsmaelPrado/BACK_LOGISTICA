import logging
from fastapi import Depends, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from app.db.database import get_db
from app.models.permiso import Permiso
from app.models.user import Usuario
from app.models.sesion import Sesion
from app.core.enums.roles_enum import UserRole

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)
# Excepción personalizada
class AdminSessionError(Exception):
    def __init__(self, detail: str):
        self.detail = detail

# Dependencia
async def admin_session_required(
    token: str = Security(api_key_header),
    db: AsyncSession = Depends(get_db)
):
    if not token:
        raise AdminSessionError("Token no proporcionado")
    # Buscar la sesión por token
    result = await db.execute(select(Sesion).where(Sesion.token == token))
    sesion = result.scalars().first()
    
    if not sesion or not sesion.estado:
        raise AdminSessionError("Sesión inválida o expirada")

    # Verificar inactividad
    if sesion.ultima_actividad + sesion.expiracion_inactividad < datetime.utcnow():
        sesion.estado = False
        await db.commit()
        raise AdminSessionError("Sesión expirada por inactividad")

    # Actualizar última actividad
    sesion.ultima_actividad = datetime.utcnow()
    await db.commit()

    # Traer usuario y validar rol
    usuario = await db.get(Usuario, sesion.id_usuario)
    if not usuario or usuario.rol != UserRole.ADMIN:
        raise AdminSessionError("No autorizado")

    return usuario


# Excepción personalizada
class UserSessionError(Exception):
    def __init__(self, detail: str):
        self.detail = detail

# Dependencia para cualquier usuario
async def user_session_required(
    token: str = Security(api_key_header),
    db: AsyncSession = Depends(get_db)
):
    if not token:
        raise UserSessionError("Token no proporcionado")
    
    # Buscar la sesión por token
    result = await db.execute(select(Sesion).where(Sesion.token == token))
    sesion = result.scalars().first()
    
    if not sesion or not sesion.estado:
        raise UserSessionError("Sesión inválida o expirada")

    # Verificar inactividad
    if sesion.ultima_actividad + sesion.expiracion_inactividad < datetime.utcnow():
        sesion.estado = False
        await db.commit()
        raise UserSessionError("Sesión expirada por inactividad")

    # Actualizar última actividad
    sesion.ultima_actividad = datetime.utcnow()
    await db.commit()

    # Traer usuario (sin validar rol)
    usuario = await db.get(Usuario, sesion.id_usuario)
    if not usuario:
        raise UserSessionError("Usuario no encontrado")

    return usuario

class PermissionDeniedError(Exception):
    def __init__(self, detail: str):
        self.detail = detail

# Dependencia para permisos específicos
def permission_required(permission_name: str):
    async def _validator(
            usuario: Usuario = Depends(user_session_required),
            db: AsyncSession = Depends(get_db)
    ):
        if usuario.rol == UserRole.ADMIN:
            return usuario  # Los admins tienen todos los permisos
        
        result = await db.execute(
            select(Permiso)
            .join(Permiso.usuarios)
            .where(Permiso.nombre == permission_name)
            .where(Usuario.id_usuario == usuario.id_usuario)
        )
        permiso = result.scalars().first()
        if not permiso:
            raise PermissionDeniedError(f"No tienes permisos para '{permission_name}'")

        return usuario
    return _validator