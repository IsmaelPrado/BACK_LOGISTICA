from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import Usuario
from app.core.security import hash_password, verify_password
from app.schemas.user import UsuarioCreate
from sqlalchemy.exc import IntegrityError
import re

async def authenticate_user(db: AsyncSession, username: str, password: str) -> Usuario | None:
    result = await db.execute(select(Usuario).filter(Usuario.nombre_usuario == username))
    user: Usuario | None = result.scalars().first()
    
    if not user:
        raise ValueError("Usuario no existe")
    if not verify_password(password, user.contrasena):
        raise ValueError("Contraseña incorrecta")
    return user


async def create_user(db: AsyncSession, user_data: UsuarioCreate) -> Usuario:
    # Validar coincidencia de contraseñas
    if user_data.contrasena != user_data.confirmar_contrasena:
        raise ValueError("Las contraseñas no coinciden.")

    # Validar fuerza de la contraseña
    pattern = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).+$')
    if not pattern.match(user_data.contrasena):
        raise ValueError(
            "La contraseña debe contener al menos una mayúscula, una minúscula, un número y un carácter especial."
        )

    # Validar correo
    email_pattern = re.compile(r'^[^@]+@[^@]+\.[^@]+$')
    if not email_pattern.match(user_data.correo_electronico):
        raise ValueError("El correo electrónico no es válido.")

    # Validar duplicados
    result = await db.execute(select(Usuario).filter(Usuario.nombre_usuario == user_data.nombre_usuario))
    if result.scalars().first():
        raise ValueError("El nombre de usuario ya está en uso.")

    result = await db.execute(select(Usuario).filter(Usuario.correo_electronico == user_data.correo_electronico))
    if result.scalars().first():
        raise ValueError("El correo electrónico ya está registrado.")

    # Crear usuario con contraseña hasheada
    nuevo = Usuario(
        nombre_usuario=user_data.nombre_usuario,
        correo_electronico=user_data.correo_electronico,
        contrasena=hash_password(user_data.contrasena),
        rol=user_data.rol
    )
    db.add(nuevo)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ValueError("No se pudo crear el usuario (conflicto en la base de datos).")

    await db.refresh(nuevo)
    return nuevo
