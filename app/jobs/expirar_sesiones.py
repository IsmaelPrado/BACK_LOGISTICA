from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from datetime import datetime
from app.models.sesion import Sesion
from app.db.database import async_session

async def expirar_sesiones():
    async with async_session() as db:
        result = await db.execute(select(Sesion).where(Sesion.estado.is_(True)))
        sesiones = result.scalars().all()
        for sesion in sesiones:
            if sesion.ultima_actividad + sesion.expiracion_inactividad < datetime.utcnow():
                sesion.estado = False
                db.add(sesion)
        await db.commit()

def iniciar_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(expirar_sesiones, "interval", minutes=1)
    scheduler.start()
    return scheduler
