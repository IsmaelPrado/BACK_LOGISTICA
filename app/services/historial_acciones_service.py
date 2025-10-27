from datetime import datetime
from sqlalchemy.orm import Session
from app.models.historial_acciones import HistorialAccion
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_
from app.models import HistorialAccion, Usuario
from app.core.enums.responses import ResponseCode
from app.schemas.api_response import PaginatedResponse, PaginationData
from app.schemas.historial_acciones import HistorialAccionItem

async def registrar_accion_async(
    db: AsyncSession,
    id_usuario: int,
    accion: str,
    modulo: str,
    descripcion: str = None,
    datos_anteriores: dict = None,
    datos_nuevos: dict = None,
):
    historial = HistorialAccion(
        id_usuario=id_usuario,
        accion=accion,
        modulo=modulo,
        descripcion=descripcion,
        datos_anteriores=datos_anteriores,
        datos_nuevos=datos_nuevos,
    )
    db.add(historial)
    await db.commit()


class HistorialService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def parse_fecha(selr, fecha_str: str) -> datetime:
        """
        Convierte un string 'dd-mm-yyyy' a datetime.
        """
        try:
            return datetime.strptime(fecha_str, "%d-%m-%Y")
        except ValueError:
            raise ValueError(f"Formato de fecha inválido: {fecha_str}. Use dd-mm-yyyy")

    async def listar_historial(
        self,
        page: int = 1,
        per_page: int = 10,
        usuario_nombre: Optional[str] = None,
        accion: Optional[str] = None,
        modulo: Optional[str] = None,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None
    ) -> PaginatedResponse[HistorialAccionItem]:
        """
        Lista el historial de acciones con filtros opcionales y paginación.
        """

        query = select(HistorialAccion).join(Usuario)

        filtros = []

        if usuario_nombre:
            filtros.append(Usuario.nombre_usuario.ilike(f"%{usuario_nombre}%"))
        if accion:
            filtros.append(HistorialAccion.accion.ilike(f"%{accion}%"))
        if modulo:
            filtros.append(HistorialAccion.modulo.ilike(f"%{modulo}%"))
        if fecha_inicio:
            if isinstance(fecha_inicio, str):
                fecha_inicio = self.parse_fecha(fecha_inicio)
            fecha_inicio = fecha_inicio.replace(tzinfo=None)
            filtros.append(HistorialAccion.fecha_accion >= fecha_inicio)

        if fecha_fin:
            if isinstance(fecha_fin, str):
                fecha_fin = self.parse_fecha(fecha_fin)
            fecha_fin = fecha_fin.replace(tzinfo=None)
            filtros.append(HistorialAccion.fecha_accion <= fecha_fin)

        if filtros:
            query = query.where(and_(*filtros))

        # Total de registros
        total_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total_items = total_result.scalar() or 0
        total_pages = (total_items // per_page) + (1 if total_items % per_page else 0)

        # Aplicar paginación
        offset = (page - 1) * per_page
        result = await self.db.execute(
            query.order_by(HistorialAccion.fecha_accion.desc()).offset(offset).limit(per_page)
        )
        items = result.scalars().all()

        # --- Convertir a Pydantic schema ---
        items_schema = [
            HistorialAccionItem(
                id_historial=h.id_historial,
                id_usuario=h.id_usuario,
                nombre_usuario=h.usuario.nombre_usuario,
                accion=h.accion,
                modulo=h.modulo,
                descripcion=h.descripcion,
                datos_anteriores=h.datos_anteriores,
                datos_nuevos=h.datos_nuevos,
                fecha_accion=h.fecha_accion
            )
            for h in items
        ]

        pagination = PaginationData(
            items=items_schema,
            page=page,
            per_page=per_page,
            total_items=total_items,
            total_pages=total_pages
        )

        return PaginatedResponse.from_enum(ResponseCode.SUCCESS, data=pagination, detail="Historial listado correctamente")
