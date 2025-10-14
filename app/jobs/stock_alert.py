from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from datetime import datetime
from app.models.product import Product
from app.models.user import Usuario
from app.services.mail_service import MailService
from app.db.database import async_session

mail_service = MailService()

async def verificar_stock_bajo():
    """
    Verifica productos con inventario menor al mínimo y envía alertas por correo a los admins.
    """
    async with async_session() as db:
        # Obtener productos con stock bajo y cargar categoría anticipadamente
        result = await db.execute(
            select(Product)
            .options(selectinload(Product.category))
            .where(Product.inventory < Product.min_inventory)
        )
        productos_bajos = result.scalars().all()

        if not productos_bajos:
            return  # nada que alertar

        # Obtener todos los usuarios con rol admin
        result_admins = await db.execute(
            select(Usuario).where(Usuario.rol == "admin")
        )
        admins = result_admins.scalars().all()
        if not admins:
            return  # no hay admins a quien notificar

        # Preparar lista de productos para el correo
        productos_data = [
            {
                "name": p.name,
                "code": p.code,
                "barcode": p.barcode or "No registrado",
                "sale_price": p.sale_price,
                "inventory": p.inventory,
                "min_inventory": p.min_inventory,
                "category": p.category.name if p.category else "Sin categoría"
            }
            for p in productos_bajos
        ]

        # Enviar un solo correo por admin con todos los productos
        for admin in admins:
            await mail_service.send_low_stock_alert(
                email=admin.correo_electronico,
                productos=productos_data,
                now=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            )


def iniciar_stock_alert_scheduler():
    """
    Inicializa el scheduler para ejecutar el job de verificación de stock bajo cada 1 minuto.
    """
    scheduler = AsyncIOScheduler()
    scheduler.add_job(verificar_stock_bajo, "interval", minutes=1, id="verificar_stock_bajo")
    scheduler.start()
    return scheduler
