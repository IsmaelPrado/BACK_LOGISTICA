from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.dependencies.auth import permission_required
from app.schemas.api_response import APIResponse
from app.schemas.historial_acciones import HistorialAccionQuery
from app.services.historial_acciones_service import HistorialService
from app.core.enums.responses import ResponseCode

router = APIRouter(prefix="/historial", tags=["historial"])

@router.post("/", status_code=status.HTTP_200_OK)
async def obtener_historial(
    request: Request,
    query: HistorialAccionQuery,  # ahora se recibe en el body
    db: AsyncSession = Depends(get_db),
    usuario = Depends(permission_required("ver_historial")),
):
    """
    Listar historial de acciones con filtros opcionales y paginación.
    """
    service = HistorialService(db)
    try:
        historial = await service.listar_historial(
            page=query.page,
            per_page=query.per_page,
            usuario_nombre=query.usuario_nombre,
            accion=query.accion,
            modulo=query.modulo,
            fecha_inicio=query.fecha_inicio,
            fecha_fin=query.fecha_fin
        )
        return historial
    except Exception as e:
        return APIResponse.from_enum(
            ResponseCode.SERVER_ERROR,
            detail=f"Ocurrió un error inesperado: {str(e)}"
        )
