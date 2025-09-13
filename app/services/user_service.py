from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import Usuario
from app.core.security import verify_password

async def authenticate_user(db: AsyncSession, username: str, password: str) -> Usuario | None:
    result = await db.execute(select(Usuario).filter(Usuario.nombre_usuario == username))
    user: Usuario | None = result.scalars().first()
    
    if not user:
        raise ValueError("Usuario no existe")
    if not verify_password(password, user.contrasena):
        raise ValueError("Contraseña incorrecta")
    return user
