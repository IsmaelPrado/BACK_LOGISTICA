import asyncio
from app.db.database import engine, Base
import app.models  # Asegurarse de que los modelos estén importados

async def init_db():
    async with engine.begin() as conn:
        # Crear tablas si no existen
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(init_db())
