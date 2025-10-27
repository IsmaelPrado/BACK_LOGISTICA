from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.dependencies.auth import permission_required
from app.schemas.api_response import APIResponse
from app.schemas.purchases import PurchaseCreateRequest, PurchaseCreateResponse
from app.services.purchase_service import PurchaseService
from app.core.enums.responses import ResponseCode

router = APIRouter(
    prefix="/purchases",
    tags=["purchases"]
)

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_purchase(
    purchase_request: PurchaseCreateRequest,
    db: AsyncSession = Depends(get_db),
    usuario = Depends(permission_required("crear_compra"))
):
    service = PurchaseService(db, usuario.id_usuario)
    try:
        purchase_result = await service.create_purchase(purchase_request)
        product_names = ", ".join([p.product for p in purchase_result.products])
        return APIResponse.from_enum(
            ResponseCode.SUCCESS,
            data=purchase_result,
            detail=f"Compra de los productos '{product_names}' registrada exitosamente."
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
