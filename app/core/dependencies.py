from datetime import datetime
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.models.sesion import Sesion
from app.models.user import Usuario
from app.services.user_service import UserService
from app.core.responses import ResponseCode

# ⚡ Aquí ponemos un tokenUrl dummy para que Swagger muestre el candado
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    # Buscar sesión por token
    result = await db.execute(
        select(Sesion).where(Sesion.token == token)
    )
    sesion = result.scalars().first()

    if not sesion or not sesion.estado:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o sesión expirada"
        )

    # Verificar expiración por inactividad
    if sesion.ultima_actividad + sesion.expiracion_inactividad < datetime.utcnow():
        sesion.estado = False
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión expirada"
        )

    # Actualizar última actividad
    sesion.ultima_actividad = datetime.utcnow()
    await db.commit()

    return sesion


