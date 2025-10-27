from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.dependencies.auth import permission_required
from app.models.category import Category
from app.models.product import Product
from app.schemas.product import ProductBase, ProductDeleteRequest, ProductPaginationRequest, ProductResponse, ProductSingleResponse, ProductUpdateRequest
from app.schemas.api_response import APIResponse, PaginatedResponse
from app.services.product_service import ProductService
from app.core.enums.responses import ResponseCode
from app.utils.decorators import log_action

router = APIRouter(prefix="/products", tags=["products"])

@router.post("/", response_model=ProductSingleResponse)
@log_action(accion="crear", modulo="productos")
async def create_product(
    product: ProductBase, 
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
@log_action(accion="eliminar", modulo="productos")
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
            previous_data=deleted_product,
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
@log_action(accion="modificar", modulo="productos")
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
         # --- Obtener producto actual ---
        result = await db.execute(select(Product).filter(Product.name == request.current_name.strip()))
        product = result.scalars().first()
        if not product:
            raise ValueError(f"No se encontró el producto con nombre '{request.current_name}'.")

        previous_data = ProductResponse(
            id_product=product.id_product,
            code=product.code,
            barcode=product.barcode,
            name=product.name,
            description=product.description,
            sale_price=product.sale_price,
            inventory=product.inventory,
            min_inventory=product.min_inventory,
            category=(await db.execute(select(Category.name).filter(Category.id == product.id_category))).scalar_one_or_none(),
            date_added=product.date_added
        )
        
        updated_product = await service.update_product_by_name(request)
        return APIResponse.from_enum(
            ResponseCode.SUCCESS,
            data=updated_product,
            previous_data=previous_data,
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