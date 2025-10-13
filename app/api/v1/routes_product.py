from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.product import ProductCreate, ProductSingleResponse
from app.schemas.api_response import APIResponse
from app.services.product_service import ProductService
from app.core.enums.responses import ResponseCode

router = APIRouter(prefix="/products", tags=["Products"])

@router.post("/", response_model=ProductSingleResponse)
async def create_product(product: ProductCreate, db: AsyncSession = Depends(get_db)):
    service = ProductService(db)

    try:
        new_product = await service.create_product(product)
        return APIResponse.from_enum(
            ResponseCode.SUCCESS,
            data=new_product,
            detail="Producto creado exitosamente."
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
