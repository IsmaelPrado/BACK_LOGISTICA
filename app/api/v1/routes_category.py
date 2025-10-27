from fastapi import APIRouter, Depends, Security
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.dependencies.auth import permission_required
from app.models.category import Category
from app.services.category_service import CategoryService
from app.schemas.category import CategoryCreate, CategoryPaginationRequest, CategoryResponse, CategorySingleResponse, CategoryUpdateRequest
from app.schemas.api_response import APIResponse, PaginatedResponse
from app.core.enums.responses import ResponseCode
from app.utils.decorators import log_action

router = APIRouter(
    prefix="/categories", 
    tags=["categories"],
    )

@router.post("/", response_model=CategorySingleResponse)
@log_action(accion="crear", modulo="categorias")
async def create_category(
    category: CategoryCreate, 
    db: AsyncSession = Depends(get_db),
    usuario=Depends(permission_required("crear_categoria"))
    ):
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
    db: AsyncSession = Depends(get_db),
    usuario=Depends(permission_required("ver_categorias"))
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

@log_action(accion="eliminar", modulo="categorias")
@router.delete("/delete", response_model=APIResponse[CategoryResponse])
async def delete_category(
    request: CategoryCreate, 
    db: AsyncSession = Depends(get_db),
    usuario=Depends(permission_required("eliminar_categoria"))
    ):
    """
    Elimina una categoría por su nombre.
    """
    service = CategoryService(db)
    try:
        deleted_category = await service.delete_category_by_name(request.name)
        return APIResponse.from_enum(
            ResponseCode.SUCCESS,
            previous_data=deleted_category,
            detail=f"Categoría '{request.name}' eliminada exitosamente."
        )

    except ValueError as e:
        detail_lower = str(e).lower()

        # Verificar tipo de error según el mensaje
        if "no se encontró" in detail_lower:
            code = ResponseCode.NOT_FOUND
        elif "productos asociados" in detail_lower:
            code = ResponseCode.CONFLICT
        else:
            code = ResponseCode.VALIDATION_ERROR

        return APIResponse.from_enum(
            code,
            detail=str(e)
        )

    except Exception as e:
        return APIResponse.from_enum(
            ResponseCode.SERVER_ERROR,
            detail=f"Ocurrió un error inesperado: {str(e)}"
        )


@router.put("/update", response_model=APIResponse
[CategoryResponse])
@log_action(accion="modificar", modulo="categorias")
async def update_category(
    request: CategoryUpdateRequest, 
    db: AsyncSession = Depends(get_db),
    usuario=Depends(permission_required("modificar_categoria"))
    ):
    service = CategoryService(db)

    try:
                # --- Obtener datos anteriores ---
        result = await db.execute(select(Category).filter(Category.name == request.current_name))
        category = result.scalars().first()

        if not category:
            raise ValueError(f"No se encontró la categoría con nombre '{request.current_name}'.")

        previous_data = CategoryResponse.from_orm(category)
        updated_category = await service.update_category_by_name(
            current_name=request.current_name,
            new_name=request.new_name
        )

        return APIResponse.from_enum(
            ResponseCode.SUCCESS,
            data=updated_category,
            previous_data=previous_data,
            detail=f"Categoría renombrada de '{request.current_name}' a '{request.new_name}' correctamente."
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
