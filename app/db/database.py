import ssl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
from typing import AsyncGenerator
import ssl

# Usamos la URL desde .env
DATABASE_URL = settings.DATABASE_URL
# Detectar si es conexión local
IS_LOCAL = "localhost" in DATABASE_URL or "127.0.0.1" in DATABASE_URL

connect_args = {}

ssl_context = ssl.create_default_context()
ssl_args = {
    "ssl": ssl_context
}
# Crear motor asíncrono

if not IS_LOCAL:
    ssl_context = ssl.create_default_context()
    connect_args = {"ssl": ssl_context}

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True,
    pool_size=50,
    max_overflow=50,
    connect_args=connect_args
)


# Crear session local
async_session = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)

# Base para modelos
Base = declarative_base()

# Dependency para obtener sesión DB
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
