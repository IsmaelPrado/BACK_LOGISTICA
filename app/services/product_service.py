from math import ceil
from typing import Optional
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from app.models.product import Product
from app.models.category import Category
from app.schemas.api_response import PaginationData
from sqlalchemy.orm import selectinload
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdateRequest


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

    async def delete_product_by_name(self, name: str) -> ProductResponse:
        """
        Elimina un producto por su nombre si existe.
        """
        name = name.strip()
        if not name:
            raise ValueError("El nombre del producto no puede estar vacío.")

        result = await self.db.execute(
            select(Product).filter(Product.name == name)
        )
        product = result.scalars().first()

        if not product:
            raise ValueError(f"No se encontró un producto con nombre '{name}'.")

        # Obtener el nombre de la categoría antes de eliminar
        result = await self.db.execute(select(Category).filter(Category.id == product.id_category))
        category = result.scalars().first()
        category_name = category.name if category else "Sin Categoría"

        await self.db.delete(product)
        await self.db.commit()

        return ProductResponse(
            id_product=product.id_product,
            code=product.code,
            barcode=product.barcode,
            name=product.name,
            description=product.description,
            sale_price=product.sale_price,
            inventory=product.inventory,
            min_inventory=product.min_inventory,
            category=category_name,
            date_added=product.date_added
        )

        
    async def update_product_by_name(self, update_data: ProductUpdateRequest) -> ProductResponse:
        """
        Actualiza un producto buscado por su nombre.
        Solo actualiza los campos que vienen con valor en la request.
        """
        current_name = update_data.current_name.strip()
        if not current_name:
            raise ValueError("El nombre actual del producto no puede estar vacío.")

        # Buscar producto exacto
        result = await self.db.execute(select(Product).filter(Product.name == current_name))
        product = result.scalars().first()
        if not product:
            raise ValueError(f"No se encontró el producto con nombre '{current_name}'.")

        # Convertimos request a dict y eliminamos campos None o strings vacías
        update_fields = {
            k: v for k, v in update_data.dict(exclude={"current_name"}).items()
            if v is not None and (not isinstance(v, str) or v.strip() != "")
        }

        # Validaciones específicas
        if "sale_price" in update_fields and update_fields["sale_price"] <= 0:
            raise ValueError("El precio debe ser mayor que cero.")
        if "inventory" in update_fields and update_fields["inventory"] < 0:
            raise ValueError("El inventario no puede ser negativo.")
        if "min_inventory" in update_fields and update_fields["min_inventory"] < 0:
            raise ValueError("El inventario mínimo no puede ser negativo.")
        if "new_name" in update_fields and len(update_fields["new_name"].strip()) < 3:
            raise ValueError("El nuevo nombre del producto debe tener al menos 3 caracteres.")
        if not update_fields:
            raise ValueError("No se proporcionaron datos válidos para actualizar el producto.")

        # Actualizar campos dinámicamente
        for field, value in update_fields.items():
            if isinstance(value, str):
                value = value.strip()
            # Mapear new_name a name
            if field == "new_name":
                setattr(product, "name", value)
            else:
                setattr(product, field, value)

        # Commit y refresco
        try:
            await self.db.commit()
            await self.db.refresh(product)
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"No se pudo actualizar el producto (conflicto en la base de datos): {e}")

        # Obtener nombre de categoría explícitamente para evitar MissingGreenlet
        result = await self.db.execute(select(Category).filter(Category.id == product.id_category))
        category = result.scalars().first()
        category_name = category.name if category else "Sin Categoría"

        return ProductResponse(
            id_product=product.id_product,
            code=product.code,
            barcode=product.barcode,
            name=product.name,
            description=product.description,
            sale_price=product.sale_price,
            inventory=product.inventory,
            min_inventory=product.min_inventory,
            category=category_name,
            date_added=product.date_added
        )
