from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.product import Product
from app.models.sales.sales import Sale
from app.models.sales.sale_items import SaleItem
from app.models.inventory_movements import InventoryMovement
from app.core.enums.tipo_movimiento import MovementType
from app.schemas.sales import SaleCreateRequest, SaleCreateResponse, SaleProductResponse  # <- tus schemas

class SaleService:
    def __init__(self, db: AsyncSession, current_user_id: int):
        self.db = db
        self.user_id = current_user_id

    async def create_sale(self, sale_request: SaleCreateRequest) -> SaleCreateResponse:
        """
        Crea una venta con múltiples productos, valida inventario, registra detalle y movimientos.
        """
        total_sale = 0
        sale_items_response = []

        # 1️⃣ Crear la venta primero
        sale = Sale(
            id_user=self.user_id,
            date=datetime.utcnow(),
            total=0,  # lo actualizamos después
            customer_name=sale_request.customer_name
        )
        self.db.add(sale)
        await self.db.flush()  # Obtener id_sale

        for item in sale_request.products:
            # 2️⃣ Buscar producto
            result = await self.db.execute(select(Product).where(Product.name == item.product_name))
            product: Product = result.scalar_one_or_none()
            if not product:
                raise ValueError(f"Producto '{item.product_name}' no encontrado")

            # 3️⃣ Validar stock
            if item.quantity > product.inventory:
                raise ValueError(f"Cantidad solicitada ({item.quantity}) mayor al stock disponible ({product.inventory})")

            previous_inventory = product.inventory
            new_inventory = previous_inventory - item.quantity

            # 4️⃣ Crear detalle de venta
            sale_item = SaleItem(
                id_sale=sale.id_sale,
                id_product=product.id_product,
                quantity=item.quantity,
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
                quantity=item.quantity,
                reason="venta",
                related_id=sale.id_sale,
                previous_inventory=previous_inventory,
                new_inventory=new_inventory,
                user_id=self.user_id,
                date=datetime.utcnow()
            )
            self.db.add(movement)

            # 7️⃣ Acumular total y preparar response
            total_sale += item.quantity * product.sale_price
            sale_items_response.append(
                SaleProductResponse(
                    product=product.name,
                    quantity=item.quantity,
                    price=float(product.sale_price),
                    previous_inventory=previous_inventory,
                    new_inventory=new_inventory,
                    min_inventory=product.min_inventory
                )
            )

        # 8️⃣ Actualizar total de la venta
        sale.total = total_sale
        await self.db.commit()
        await self.db.refresh(sale)

        # 9️⃣ Retornar response tipado
        return SaleCreateResponse(
            sale_id=sale.id_sale,
            total=float(total_sale),
            date=sale.date,
            customer_name=sale.customer_name,
            products=sale_items_response
        )
