from math import ceil
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from app.models.category import Category
from app.schemas.api_response import PaginationData
from app.schemas.category import CategoryCreate, CategoryResponse
from pydantic import parse_obj_as


class CategoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_category(self, category_data: CategoryCreate) -> CategoryResponse:
        """
        Crea una nueva categoría validando duplicados y campos requeridos.
        """

        # 🔹 Validación de nombre
        if not category_data.name or not category_data.name.strip():
            raise ValueError("El nombre de la categoría no puede estar vacío.")
        if len(category_data.name.strip()) < 3:
            raise ValueError("El nombre de la categoría debe tener al menos 3 caracteres.")

        # 🔹 Validar duplicados (nombre único)
        result = await self.db.execute(
            select(Category).filter(Category.name == category_data.name.strip())
        )
        if result.scalars().first():
            raise ValueError("Ya existe una categoría con ese nombre.")

        # 🔹 Crear nueva categoría
        nueva_categoria = Category(
            name=category_data.name.strip()
        )
        self.db.add(nueva_categoria)

        try:
            await self.db.flush()
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise ValueError("No se pudo crear la categoría (conflicto en la base de datos).")

        await self.db.refresh(nueva_categoria)
        return CategoryResponse.from_orm(nueva_categoria)


 # Método para paginación
    async def get_categories_paginated(self, page: int, per_page: int):
        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 10

        total_result = await self.db.execute(select(Category))
        total_items = len(total_result.scalars().all())

        offset = (page - 1) * per_page
        result = await self.db.execute(select(Category).offset(offset).limit(per_page))
        categories = result.scalars().all()

        items = [CategoryResponse.from_orm(cat) for cat in categories]
        total_pages = ceil(total_items / per_page) if total_items else 1

        return PaginationData[CategoryResponse](
            items=items,
            page=page,
            per_page=per_page,
            total_items=total_items,
            total_pages=total_pages
        )
