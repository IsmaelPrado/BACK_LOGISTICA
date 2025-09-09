from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Usamos la URL desde .env
DATABASE_URL = settings.DATABASE_URL


# Crear motor asíncrono
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# Crear session local
async_session = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)

# Base para modelos
Base = declarative_base()
