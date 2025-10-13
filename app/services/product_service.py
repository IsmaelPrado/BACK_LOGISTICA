from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from app.models.product import Product
from app.models.category import Category
from app.schemas.product import ProductCreate, ProductResponse

class ProductService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_product(self, product_data: ProductCreate) -> ProductResponse:
        """
        Crea un nuevo producto validando código único y categoría existente.
        """

        # Validar categoría existente
        result = await self.db.execute(select(Category).filter(Category.id == product_data.id_category))
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
            id_category=product_data.id_category
        )

        self.db.add(nuevo_producto)

        try:
            await self.db.flush()
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise ValueError("Error al registrar el producto. Verifique los datos.")
        
        await self.db.refresh(nuevo_producto)
        return ProductResponse.from_orm(nuevo_producto)
