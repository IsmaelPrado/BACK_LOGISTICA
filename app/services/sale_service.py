from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.product import Product
from app.models.sales.sales import Sale
from app.models.sales.sale_items import SaleItem
from app.models.inventory_movements import InventoryMovement
from app.core.enums.tipo_movimiento import MovementType
from app.schemas.sales import SaleCreateRequest, SaleCreateResponse  # <- tus schemas

class SaleService:
    def __init__(self, db: AsyncSession, current_user_id: int):
        self.db = db
        self.user_id = current_user_id

    async def create_sale(self, sale_request: SaleCreateRequest) -> SaleCreateResponse:
        """
        Crea una venta, valida inventario, registra detalle y movimiento de inventario.
        """
        # 1️⃣ Buscar producto
        result = await self.db.execute(select(Product).where(Product.name == sale_request.product_name))
        product: Product = result.scalar_one_or_none()

        if not product:
            raise ValueError(f"Producto '{sale_request.product_name}' no encontrado")

        # 2️⃣ Validar stock
        if sale_request.quantity > product.inventory:
            raise ValueError(f"Cantidad solicitada ({sale_request.quantity}) mayor al stock disponible ({product.inventory})")

        previous_inventory = product.inventory
        new_inventory = previous_inventory - sale_request.quantity

        # 3️⃣ Crear la venta
        sale = Sale(
            id_user=self.user_id,
            date=datetime.utcnow(),
            total=product.sale_price * sale_request.quantity,
            customer_name=sale_request.customer_name
        )
        self.db.add(sale)
        await self.db.flush()  # Necesario para obtener el id_sale

        # 4️⃣ Crear detalle de venta
        sale_item = SaleItem(
            id_sale=sale.id_sale,
            id_product=product.id_product,
            quantity=sale_request.quantity,
            price=product.sale_price
        )
        self.db.add(sale_item)

        # 5️⃣ Actualizar inventario del producto
        product.inventory = new_inventory
        self.db.add(product)

        # 6️⃣ Registrar movimiento de inventario
        movement = InventoryMovement(
            id_product=product.id_product,
            movement_type=MovementType.SALIDA,
            quantity=sale_request.quantity,
            reason="venta",
            related_id=sale.id_sale,
            previous_inventory=previous_inventory,
            new_inventory=new_inventory,
            user_id=self.user_id,
            date=datetime.utcnow()
        )
        self.db.add(movement)

        # 7️⃣ Guardar cambios
        await self.db.commit()
        await self.db.refresh(sale)

        # 8️⃣ Retornar response tipado
        return SaleCreateResponse(
            sale_id=sale.id_sale,
            product=product.name,
            quantity=sale_request.quantity,
            total=float(sale.total),
            previous_inventory=previous_inventory,
            new_inventory=new_inventory,
            date=datetime.utcnow()
        )
