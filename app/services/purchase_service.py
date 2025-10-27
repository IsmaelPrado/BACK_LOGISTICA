import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.product import Product
from app.models.purchases.purchases import Purchase
from app.models.purchases.purchase_items import PurchaseItem
from app.models.inventory_movements import InventoryMovement
from app.core.enums.tipo_movimiento import MovementType
from app.schemas.purchases import PurchaseCreateRequest, PurchaseCreateResponse, PurchaseProductResponse
from app.services.mail_service import MailService  # Opcional: si quieres alertas de inventario

class PurchaseService:
    def __init__(self, db: AsyncSession, current_user_id: int):
        self.db = db
        self.user_id = current_user_id

    async def create_purchase(self, purchase_request: PurchaseCreateRequest) -> PurchaseCreateResponse:
        total_purchase = 0
        purchase_items_response = []

        # 1️⃣ Crear la compra
        purchase = Purchase(
            id_user=self.user_id,
            date=datetime.utcnow(),
            total=0,
            supplier_name=purchase_request.supplier_name
        )
        self.db.add(purchase)
        await self.db.flush()  # Para obtener el ID antes del commit

        # 2️⃣ Iterar productos
        for item in purchase_request.products:
            result = await self.db.execute(
                select(Product).where(Product.name == item.product_name).options(selectinload(Product.category))
            )
            product: Product = result.scalar_one_or_none()
            if not product:
                raise ValueError(f"Producto '{item.product_name}' no encontrado")

            previous_inventory = product.inventory
            new_inventory = previous_inventory + item.quantity  # ✅ Sumar al inventario

            # 3️⃣ Detalle de compra
            purchase_item = PurchaseItem(
                id_purchase=purchase.id_purchase,
                id_product=product.id_product,
                quantity=item.quantity,
                price=item.price
            )
            self.db.add(purchase_item)

            # 4️⃣ Actualizar inventario
            product.inventory = new_inventory
            self.db.add(product)

            # 5️⃣ Movimiento de inventario
            movement = InventoryMovement(
                id_product=product.id_product,
                movement_type=MovementType.ENTRADA,
                quantity=item.quantity,
                reason="compra",
                related_id=purchase.id_purchase,
                previous_inventory=previous_inventory,
                new_inventory=new_inventory,
                user_id=self.user_id,
                date=datetime.utcnow()
            )
            self.db.add(movement)

            total_purchase += item.quantity * item.price
            purchase_items_response.append(
                PurchaseProductResponse(
                    product=product.name,
                    quantity=item.quantity,
                    price=float(item.price),
                    previous_inventory=previous_inventory,
                    new_inventory=new_inventory
                )
            )

        # 6️⃣ Confirmar compra
        purchase.total = total_purchase
        await self.db.commit()
        await self.db.refresh(purchase)

        # 7️⃣ Retornar response
        return PurchaseCreateResponse(
            purchase_id=purchase.id_purchase,
            total=float(total_purchase),
            date=purchase.date,
            supplier_name=purchase.supplier_name,
            products=purchase_items_response
        )
