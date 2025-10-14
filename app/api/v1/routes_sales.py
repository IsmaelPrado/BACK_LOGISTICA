from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db  # Tu función de dependencia para obtener la sesión
from app.dependencies.auth import permission_required
from app.schemas.api_response import APIResponse
from app.schemas.sales import SaleCreateRequest, SaleCreateResponse
from app.services.sale_service import SaleService
from app.core.enums.responses import ResponseCode

router = APIRouter(
    prefix="/sales",
    tags=["sales"]
)

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_sale(
    sale_request: SaleCreateRequest,
    db: AsyncSession = Depends(get_db),
    usuario = Depends(permission_required("crear_venta"))
):
    service = SaleService(db, usuario.id_usuario)
    try:
        sale_result = await service.create_sale(sale_request)
        product_names = ", ".join([p.product_name for p in sale_request.products])
        return APIResponse.from_enum(
            ResponseCode.SUCCESS,
            data=sale_result,
            detail=f"Venta de los productos '{product_names}' registrada exitosamente."
        )
    except ValueError as e:
        return APIResponse.from_enum(
            ResponseCode.VALIDATION_ERROR,
            detail=str(e)
        )
    except Exception as e:
        return APIResponse.from_enum(
            ResponseCode.SERVER_ERROR,
            detail=f"Ocurrió un error inesperado: {str(e)}"
        )