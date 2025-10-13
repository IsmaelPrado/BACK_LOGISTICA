from math import ceil
from typing import Optional
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from app.models.product import Product
from app.models.category import Category
from app.schemas.api_response import PaginationData
from app.schemas.product import ProductCreate, ProductResponse
from sqlalchemy.orm import selectinload

class ProductService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_product(self, product_data: ProductCreate) -> ProductResponse:
        """
        Crea un nuevo producto validando código único y categoría existente.
        """

        # Validar categoría existente
        result = await self.db.execute(select(Category).filter(Category.name == product_data.category))
        category = result.scalars().first()
        if not category:
            raise ValueError("La categoría especificada no existe.")

        # Validar duplicado de código
        result = await self.db.execute(select(Product).filter(Product.code == product_data.code))
        if result.scalars().first():
            raise ValueError("Ya existe un producto con ese código.")

        # Crear producto
        nuevo_producto = Product(
            code=product_data.code,
            barcode=product_data.barcode,
            name=product_data.name,
            description=product_data.description,
            sale_price=product_data.sale_price,
            inventory=product_data.inventory,
            min_inventory=product_data.min_inventory,
            id_category=category.id
        )

        self.db.add(nuevo_producto)

        try:
            await self.db.flush()
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise ValueError("Error al registrar el producto. Verifique los datos.")
        
        await self.db.refresh(nuevo_producto)
        return ProductResponse(
            id_product=nuevo_producto.id_product,
            code=nuevo_producto.code,
            barcode=nuevo_producto.barcode,
            name=nuevo_producto.name,
            description=nuevo_producto.description,
            sale_price=nuevo_producto.sale_price,
            inventory=nuevo_producto.inventory,
            min_inventory=nuevo_producto.min_inventory,
            category=category.name,
            date_added=nuevo_producto.date_added
        )

    # Método para paginación de productos
    async def get_products_paginated(
        self,
        page: int,
        per_page: int,
        category_name: Optional[str] = None,
        product_name: Optional[str] = None
    ):
        # Validación básica de página y cantidad por página
        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 10

        # Query base con join a Category
        query = (
            select(Product)
            .options(selectinload(Product.category))
            .join(Category)
        )

        # Filtro opcional por nombre de categoría (case-insensitive)
        if category_name:
            query = query.where(func.lower(Category.name) == category_name.lower())

        # Filtro opcional por nombre del producto (case-insensitive, búsqueda por palabra clave)
        if product_name:
            query = query.where(func.lower(Product.name).like(f"%{product_name.lower()}%"))

        # Total de productos
        total_result = await self.db.execute(query)
        total_items = len(total_result.scalars().all())

        # Paginación
        offset = (page - 1) * per_page
        result = await self.db.execute(
            query.order_by(Category.name, Product.id_product)
                .offset(offset)
                .limit(per_page)
        )
        products = result.scalars().all()

        # Convertir a schema
        items = [
            ProductResponse(
                id_product=prod.id_product,
                code=prod.code,
                barcode=prod.barcode,
                name=prod.name,
                description=prod.description,
                sale_price=prod.sale_price,
                inventory=prod.inventory,
                min_inventory=prod.min_inventory,
                category=prod.category.name if prod.category else "Sin Categoría",
                date_added=prod.date_added
            ) 
            for prod in products
        ]
        total_pages = ceil(total_items / per_page) if total_items else 1

        return PaginationData[ProductResponse](
            items=items,
            page=page,
            per_page=per_page,
            total_items=total_items,
            total_pages=total_pages
        )
