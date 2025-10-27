from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime
from decimal import Decimal
from typing import List

from app.models import Sale, SaleItem, Product, Usuario, Category
from app.schemas.reporte_ventas import (
    ReporteVentasRequest,
    ReporteVentasResponse,
    VentaReporte,
    ProductoReporte
)


async def generar_reporte_ventas(db: AsyncSession, filtros: ReporteVentasRequest) -> ReporteVentasResponse:
    """
    Genera un reporte de ventas con filtros opcionales:
    - Lista de nombres de usuarios o todos
    - Rango de fechas
    - Categorías
    - Productos
    """

    # 🔹 Consulta base con relaciones cargadas
    query = (
        select(Sale)
        .options(
            selectinload(Sale.items)
            .selectinload(SaleItem.product)
            .selectinload(Product.category),
            selectinload(Sale.usuario)
        )
        .join(Usuario, Usuario.id_usuario == Sale.id_user)
    )

    condiciones = []

    # 🔹 Fechas (manejo seguro)
    fecha_inicio = None
    fecha_fin = None
    if filtros.fecha_inicio:
        try:
            fecha_inicio = datetime.fromisoformat(filtros.fecha_inicio)
        except ValueError:
            raise ValueError("El formato de fecha_inicio no es válido. Usa ISO 8601 (YYYY-MM-DD).")

    if filtros.fecha_fin:
        try:
            fecha_fin = datetime.fromisoformat(filtros.fecha_fin)
        except ValueError:
            raise ValueError("El formato de fecha_fin no es válido. Usa ISO 8601 (YYYY-MM-DD).")

    # 🔹 Filtro por usuarios (lista de nombres)
    if filtros.nombres_usuario and len(filtros.nombres_usuario) > 0:
        condiciones.append(Usuario.nombre_usuario.in_(filtros.nombres_usuario))

    # 🔹 Filtros de fecha
    if fecha_inicio and fecha_fin:
        condiciones.append(and_(Sale.date >= fecha_inicio, Sale.date <= fecha_fin))
    elif fecha_inicio:
        condiciones.append(Sale.date >= fecha_inicio)
    elif fecha_fin:
        condiciones.append(Sale.date <= fecha_fin)

    # 🔹 Aplicar condiciones
    if condiciones:
        query = query.filter(and_(*condiciones))

    # 🔹 Ejecutar consulta
    result = await db.execute(query)
    ventas = result.scalars().unique().all()

    resultado: List[VentaReporte] = []
    total_general = Decimal("0.00")

    # 🔹 Procesar ventas
    for venta in ventas:
        productos: List[ProductoReporte] = []
        subtotal_venta = Decimal("0.00")

        for item in venta.items:
            producto = item.product
            categoria = producto.category

            # Filtros adicionales
            if filtros.categorias and categoria.name not in filtros.categorias:
                continue
            if filtros.productos and producto.name not in filtros.productos:
                continue

            subtotal = item.price * item.quantity
            subtotal_venta += subtotal

            productos.append(
                ProductoReporte(
                    id_product=producto.id_product,
                    nombre=producto.name,
                    categoria=categoria.name,
                    cantidad=item.quantity,
                    precio_unitario=item.price,
                    subtotal=subtotal
                )
            )

        if not productos:
            continue

        venta_reporte = VentaReporte(
            id_sale=venta.id_sale,
            fecha=venta.date,
            usuario=venta.usuario.nombre_usuario if venta.usuario else f"ID {venta.id_user}",
            cliente=venta.customer_name,
            total=venta.total,
            productos=productos
        )

        resultado.append(venta_reporte)
        total_general += venta.total

    return ReporteVentasResponse(
        ventas=resultado,
        total_general=total_general,
        total_ventas=len(resultado)
    )