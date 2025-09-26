from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.sesion import Sesion
from datetime import datetime, timedelta

class SessionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def crear_o_actualizar_sesion(
        self,
        id_usuario: int,
        latitud: float | None = None,
        longitud: float | None = None
    ) -> tuple[Sesion, bool, Optional[int]]:
        """
        Retorna (sesion, creada/nueva, tiempo_restante)
        - Si ya hay una sesión activa y no ha expirado → actualiza ultima_actividad, retorna False y tiempo_restante
        - Si no hay sesión activa o expiró → crea/actualiza y retorna True y tiempo_restante
        """
        result = await self.db.execute(
            select(Sesion).where(Sesion.id_usuario == id_usuario)
        )
        sesion_existente = result.scalars().first()

        ahora = datetime.utcnow()

        if sesion_existente:
            expiracion = sesion_existente.ultima_actividad + sesion_existente.expiracion_inactividad

            if sesion_existente.estado and ahora <= expiracion:
                # 🔄 Sesión activa: actualizar última actividad (resetea el tiempo de expiración)
                sesion_existente.ultima_actividad = ahora
                sesion_existente.latitud = latitud
                sesion_existente.longitud = longitud

                self.db.add(sesion_existente)
                await self.db.commit()
                await self.db.refresh(sesion_existente)

                # recalcular expiración usando la nueva ultima_actividad
                expiracion = sesion_existente.ultima_actividad + sesion_existente.expiracion_inactividad
                tiempo_restante = int((expiracion - ahora).total_seconds())
                return sesion_existente, False, tiempo_restante

            # ⏳ Sesión expiró: reactivar
            sesion_existente.fecha_inicio = ahora
            sesion_existente.ultima_actividad = ahora
            sesion_existente.estado = True
            sesion_existente.latitud = latitud
            sesion_existente.longitud = longitud

            self.db.add(sesion_existente)
            await self.db.commit()
            await self.db.refresh(sesion_existente)

            tiempo_restante = int(sesion_existente.expiracion_inactividad.total_seconds())
            return sesion_existente, True, tiempo_restante

        # 🔹 No existe: crear nueva sesión
        nueva_sesion = Sesion(
            id_usuario=id_usuario,
            fecha_inicio=ahora,
            ultima_actividad=ahora,
            estado=True,
            latitud=latitud,
            longitud=longitud
        )
        self.db.add(nueva_sesion)
        await self.db.commit()
        await self.db.refresh(nueva_sesion)

        tiempo_restante = int(nueva_sesion.expiracion_inactividad.total_seconds())
        return nueva_sesion, True, tiempo_restante



    async def validar_sesion(self, id_sesion: int) -> bool:
        """Valida si la sesión sigue activa y no ha expirado por inactividad"""
        result = await self.db.execute(
            select(Sesion).where(Sesion.id == id_sesion)
        )
        sesion = result.scalars().first()
        if not sesion or sesion.estado != True:
            return False

        # Verificar inactividad
        if sesion.ultima_actividad + sesion.expiracion_inactividad < datetime.utcnow():
            sesion.estado = False
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
            sesion.estado = False
            await self.db.commit()
