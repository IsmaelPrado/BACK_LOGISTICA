from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.dependencies.auth import permission_required
from app.schemas.product import ProductCreate, ProductDeleteRequest, ProductPaginationRequest, ProductResponse, ProductSingleResponse, ProductUpdateRequest
from app.schemas.api_response import APIResponse, PaginatedResponse
from app.services.product_service import ProductService
from app.core.enums.responses import ResponseCode

router = APIRouter(prefix="/products", tags=["products"])

@router.post("/", response_model=ProductSingleResponse)
async def create_product(
    product: ProductCreate, 
    db: AsyncSession = Depends(get_db),
    usuario=Depends(permission_required("crear_producto"))
    ):
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


@router.post("/paginated", response_model=PaginatedResponse[ProductResponse])
async def get_products_paginated(
    request: ProductPaginationRequest,
    db: AsyncSession = Depends(get_db),
    usuario=Depends(permission_required("ver_productos"))
):
    service = ProductService(db)
    try:
        # Llamada al service para obtener productos paginados
        pagination_data = await service.get_products_paginated(
            page=request.page,
            per_page=request.per_page,
            category_name=request.category_name,  # ahora se filtra por nombre
            product_name=request.product_name     # filtro opcional por palabra clave
        )

        return PaginatedResponse[ProductResponse].from_enum(
            ResponseCode.SUCCESS,
            data=pagination_data,
            detail="Listado de productos paginado correctamente y ordenado por categoría."
        )

    except Exception as e:
        return PaginatedResponse[ProductResponse].from_enum(
            ResponseCode.SERVER_ERROR,
            detail=f"Ocurrió un error inesperado: {str(e)}"
        )


@router.delete("/delete", response_model=APIResponse[ProductResponse])
async def delete_product(
    request: ProductDeleteRequest, 
    db: AsyncSession = Depends(get_db),
    usuario=Depends(permission_required("eliminar_producto"))
    ):
    """
    Elimina un producto por su nombre.
    """
    service = ProductService(db)
    try:
        deleted_product = await service.delete_product_by_name(request.name)
        return APIResponse.from_enum(
            ResponseCode.SUCCESS,
            data=deleted_product,
            detail=f"Producto '{request.name}' eliminado exitosamente."
        )
    except ValueError as e:
        return APIResponse.from_enum(
            ResponseCode.NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        return APIResponse.from_enum(
            ResponseCode.SERVER_ERROR,
            detail=f"Ocurrió un error inesperado: {str(e)}"
        )
        
@router.put("/update", response_model=ProductSingleResponse)
async def update_product(
    request: ProductUpdateRequest, 
    db: AsyncSession = Depends(get_db),
    usuario=Depends(permission_required("modificar_producto"))
):
    """
    Actualiza los datos de un producto buscado por su nombre.
    """
    service = ProductService(db)

    try:
        updated_product = await service.update_product_by_name(request)
        return APIResponse.from_enum(
            ResponseCode.SUCCESS,
            data=updated_product,
            detail=f"Producto '{request.current_name}' actualizado exitosamente."
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