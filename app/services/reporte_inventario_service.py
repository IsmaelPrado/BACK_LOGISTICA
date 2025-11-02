from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from app.models import Product, Category, InventoryMovement
from app.core.enums.tipo_movimiento import MovementType
from app.core.enums.tipo_inventario import InventoryFilterType
from app.schemas.reporte_inventario import (
    ReporteInventarioRequest,
    ReporteInventarioResponse,
    ProductoInventario
)


async def generar_reporte_inventario(db, filtros: ReporteInventarioRequest) -> ReporteInventarioResponse:
    """
    Genera un reporte de inventario filtrado por:
    - Categorías
    - Productos específicos
    - Tipo de inventario (bajo, bueno o todos)
    """

    # ✅ Cargar categoría sin lazy load (evita greenlet error)
    query = select(Product).options(selectinload(Product.category)).join(Category)
    condiciones = []

    # 🔹 Filtrar por categorías
    if filtros.categorias:
        condiciones.append(Category.name.in_(filtros.categorias))

    # 🔹 Filtrar por productos
    if filtros.productos:
        condiciones.append(Product.name.in_(filtros.productos))

    # 🔹 Filtro por tipo de inventario (Enum)
    if filtros.tipo_inventario == InventoryFilterType.bajo:
        condiciones.append(Product.inventory <= Product.min_inventory)
    elif filtros.tipo_inventario == InventoryFilterType.bueno:
        condiciones.append(Product.inventory > Product.min_inventory)
    # Si es "todos", no agregamos filtro

    # 🔹 Aplicar condiciones al query
    if condiciones:
        query = query.filter(and_(*condiciones))

    result = await db.execute(query)
    productos = result.scalars().all()

    reporte = []
    total_stock_general = 0

    for producto in productos:
        # Movimientos asociados (para mostrar totales)
        mov_query = select(InventoryMovement).filter(InventoryMovement.id_product == producto.id_product)
        movimientos: list[InventoryMovement] = (await db.execute(mov_query)).scalars().all()

        entradas = sum(m.quantity for m in movimientos if m.movement_type == MovementType.ENTRADA)
        salidas = sum(m.quantity for m in movimientos if m.movement_type == MovementType.SALIDA)
        ultima_actualizacion = max((m.date for m in movimientos), default=None)

        total_stock_general += producto.inventory

        reporte.append(
            ProductoInventario(
                id_product=producto.id_product,
                nombre=producto.name,
                categoria=producto.category.name if producto.category else "Sin categoría",
                total_entradas=entradas,
                total_salidas=salidas,
                stock_actual=producto.inventory,
                minimo=producto.min_inventory,
                ultima_actualizacion=ultima_actualizacion
            )
        )


    return ReporteInventarioResponse(
        productos=reporte,
        total_productos=len(reporte),
        total_stock_general=total_stock_general
    )
