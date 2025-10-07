from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.services.category_service import CategoryService
from app.schemas.category import CategoryCreate, CategoryPaginationRequest, CategoryResponse, CategorySingleResponse
from app.schemas.api_response import APIResponse, PaginatedResponse
from app.core.responses import ResponseCode

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.post("/", response_model=CategorySingleResponse)
async def create_category(category: CategoryCreate, db: AsyncSession = Depends(get_db)):
    service = CategoryService(db)

    try:
        # Crear la categoría mediante el servicio
        new_category = await service.create_category(category)

        # Retornar respuesta exitosa
        return APIResponse.from_enum(
            ResponseCode.SUCCESS,
            data=new_category,
            detail="Categoría creada exitosamente."
        )

    except ValueError as e:
        # Error de validación o duplicado
        return APIResponse.from_enum(
            ResponseCode.VALIDATION_ERROR,
            detail=str(e)
        )

    except Exception as e:
        # Error inesperado del servidor
        return APIResponse.from_enum(
            ResponseCode.SERVER_ERROR,
            detail=f"Ocurrió un error inesperado: {str(e)}"
        )
        
@router.post("/paginated", response_model=PaginatedResponse[CategoryResponse])
async def get_categories_paginated(
    request: CategoryPaginationRequest,
    db: AsyncSession = Depends(get_db)
):
    service = CategoryService(db)
    try:
        pagination_data = await service.get_categories_paginated(request.page, request.per_page)
        return PaginatedResponse[CategoryResponse].from_enum(
            ResponseCode.SUCCESS,
            data=pagination_data,
            detail="Listado de categorías paginado correctamente."
        )
    except Exception as e:
        return PaginatedResponse[CategoryResponse].from_enum(
            ResponseCode.SERVER_ERROR,
            detail=f"Ocurrió un error inesperado: {str(e)}"
        )
