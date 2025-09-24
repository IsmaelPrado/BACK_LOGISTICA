from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.sesion import Sesion
from datetime import datetime, timedelta

class SessionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def crear_sesion(self, id_usuario: int, latitud: float | None = None, longitud: float | None = None) -> Sesion:
        # 1️⃣ Cerrar sesiones activas existentes
        await self.db.execute(
            update(Sesion)
            .where(Sesion.id_usuario == id_usuario, Sesion.estado == "activa")
            .values(estado="cerrada")
        )

        # 2️⃣ Crear nueva sesión
        nueva_sesion = Sesion(
            id_usuario=id_usuario,
            fecha_inicio=datetime.utcnow(),
            ultima_actividad=datetime.utcnow(),
            estado="activa",
            latitud=latitud,
            longitud=longitud
        )

        self.db.add(nueva_sesion)
        await self.db.commit()
        await self.db.refresh(nueva_sesion)
        return nueva_sesion

    async def validar_sesion(self, id_sesion: int) -> bool:
        """Valida si la sesión sigue activa y no ha expirado por inactividad"""
        result = await self.db.execute(
            select(Sesion).where(Sesion.id == id_sesion)
        )
        sesion = result.scalars().first()
        if not sesion or sesion.estado != "activa":
            return False

        # Verificar inactividad
        if sesion.ultima_actividad + sesion.expiracion_inactividad < datetime.utcnow():
            sesion.estado = "expirada"
            await self.db.commit()
            return False

        # Actualizar última actividad
        sesion.ultima_actividad = datetime.utcnow()
        await self.db.commit()
        return True

    async def cerrar_sesion(self, id_sesion: int):
        result = await self.db.execute(
            select(Sesion).where(Sesion.id == id_sesion)
        )
        sesion = result.scalars().first()
        if sesion:
            sesion.estado = "cerrada"
            await self.db.commit()
