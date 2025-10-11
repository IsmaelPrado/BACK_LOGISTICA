from fastapi import Depends, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from app.db.database import get_db
from app.models.user import Usuario
from app.models.sesion import Sesion
from app.core.enums.roles_enum import UserRole

api_key_header = APIKeyHeader(name="Token", auto_error=False)
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
