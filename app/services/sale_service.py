import asyncio
from datetime import datetime
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.product import Product
from app.models.sales.sales import Sale
from app.models.sales.sale_items import SaleItem
from app.models.inventory_movements import InventoryMovement
from app.core.enums.tipo_movimiento import MovementType
from app.schemas.sales import SaleCreateRequest, SaleCreateResponse, SaleProductResponse
from app.services.mail_service import MailService  # <- tus schemas
from sqlalchemy.orm import selectinload

class SaleService:
    def __init__(self, db: AsyncSession, current_user_id: int):
        self.db = db
        self.user_id = current_user_id

    async def create_sale(self, sale_request: SaleCreateRequest) -> SaleCreateResponse:
        """
        Crea una venta con múltiples productos, valida inventario, registra detalle y movimientos.
        También envía alerta por correo si algún producto queda bajo el inventario mínimo.
        """
        total_sale = 0
        sale_items_response = []
        productos_bajo_minimo = []

        # 1️⃣ Crear la venta
        sale = Sale(
            id_user=self.user_id,
            date=datetime.utcnow(),
            total=0,
            customer_name=sale_request.customer_name
        )
        self.db.add(sale)
        await self.db.flush()  # Para obtener el ID antes del commit

        for item in sale_request.products:
            query = select(Product).options(selectinload(Product.category))
            query = query.where(
                or_(
                    Product.barcode == item.barcode,
                    Product.code == item.product_code
                )
            )
            
            result = await self.db.execute(query)
            product: Product = result.scalar_one_or_none()
            if not product:
                raise ValueError(f"Producto con código '{item.product_code or item.barcode}' no encontrado.")


            if item.quantity > product.inventory:
                raise ValueError(f"Cantidad solicitada ({item.quantity}) mayor al stock disponible ({product.inventory})")

            previous_inventory = product.inventory
            new_inventory = previous_inventory - item.quantity

            # Detalle de venta
            sale_item = SaleItem(
                id_sale=sale.id_sale,
                id_product=product.id_product,
                quantity=item.quantity,
                price=product.sale_price
            )
            self.db.add(sale_item)

            # Actualizar inventario
            product.inventory = new_inventory
            self.db.add(product)

            # Movimiento de inventario
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

            # Alerta de stock bajo
            if new_inventory < product.min_inventory:
                productos_bajo_minimo.append({
                    "name": product.name,
                    "code": product.code,
                    "barcode": product.barcode,
                    "sale_price": float(product.sale_price),
                    "inventory": new_inventory,
                    "min_inventory": product.min_inventory,
                    "category": product.category.name if product.category else "Sin categoría"
                })

        # 9️⃣ Confirmar venta
        sale.total = total_sale
        await self.db.commit()
        await self.db.refresh(sale)

        # 🔹 Enviar correo asíncrono en background (sin bloquear ni tocar la sesión)
        if productos_bajo_minimo:
            asyncio.create_task(
                MailService().send_stock_alert_email(
                    email="vansestilo200@gmail.com",
                    productos=productos_bajo_minimo
                )
            )

        # 10️⃣ Retornar response
        return SaleCreateResponse(
            sale_id=sale.id_sale,
            total=float(total_sale),
            date=sale.date,
            customer_name=sale.customer_name,
            products=sale_items_response,
            low_stock_products=productos_bajo_minimo
        )