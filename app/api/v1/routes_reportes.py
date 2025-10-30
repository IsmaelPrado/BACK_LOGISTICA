from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.reporte_ventas import ReporteVentasRequest, ReporteVentasResponse
from app.services.reporte_ventas_service import generar_reporte_ventas
from app.schemas.api_response import APIResponse, ResponseCode
from app.dependencies.auth import permission_required

router = APIRouter(prefix="/reportes", tags=["Reportes"])

@router.post("/ventas", response_model=APIResponse[ReporteVentasResponse])
async def obtener_reporte_ventas(
    filtros: ReporteVentasRequest,
    db: AsyncSession = Depends(get_db),
    usuario=Depends(permission_required("ver_reportes"))
):
    """
    📊 Endpoint para generar un reporte de ventas filtrado por usuario, fechas, categorías o productos.
    """
    try:
        # Llamar al servicio con los filtros
        reporte = await generar_reporte_ventas(db, filtros)

        return APIResponse.from_enum(
            ResponseCode.SUCCESS,
            data=reporte,
            detail="Reporte de ventas generado correctamente."
        )

    except ValueError as e:
        return APIResponse.from_enum(
            ResponseCode.VALIDATION_ERROR,
            detail=str(e)
        )
    except Exception as e:
        return APIResponse.from_enum(
            ResponseCode.SERVER_ERROR,
            detail=f"Ocurrió un error al generar el reporte: {str(e)}"
        )
