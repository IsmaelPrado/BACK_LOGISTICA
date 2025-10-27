from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel
from datetime import date, datetime

class ReporteVentasRequest(BaseModel):
    nombres_usuario: Optional[List[str]] = None                  # Si se omite, se muestran todas las ventas
    fecha_inicio: Optional[str] = None               # Rango de fechas
    fecha_fin: Optional[str] = None
    categorias: Optional[List[str]] = None            # Nombres de categorías a filtrar
    productos: Optional[List[str]] = None             # Nombres de productos a filtrar


class ProductoReporte(BaseModel):
    id_product: int
    nombre: str
    categoria: str
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal

class VentaReporte(BaseModel):
    id_sale: int
    fecha: datetime
    usuario: str
    cliente: Optional[str]
    total: Decimal
    productos: List[ProductoReporte]

class ReporteVentasResponse(BaseModel):
    ventas: List[VentaReporte]
    total_general: Decimal
    total_ventas: int