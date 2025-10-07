# app/dependencies/auth.py
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from app.db.database import get_db
from app.models.user import Usuario
from app.models.sesion import Sesion

# Excepción personalizada
class AdminSessionError(Exception):
    def __init__(self, detail: str):
        self.detail = detail

# Dependencia
async def admin_session_required(
    token: str = Header(..., description="Token de sesión del usuario"),
    db: AsyncSession = Depends(get_db)
):
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
    if not usuario or usuario.rol != "admin":
        raise AdminSessionError("No autorizado")

    return usuario
