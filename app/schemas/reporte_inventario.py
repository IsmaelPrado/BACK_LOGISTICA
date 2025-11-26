from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from app.validators.common_validators import traducir_error_lista, validar_tipo_inventario

class ReporteInventarioRequest(BaseModel):
    categorias: Optional[List[str]] = None
    productos: Optional[List[str]] = None
    tipo_inventario: str = "todos"

    # Aplicamos el validador externo
    _validar_tipo_inventario = validar_tipo_inventario()
    _traducir_error_lista_categorias = traducir_error_lista("categorias")
    _traducir_error_lista_productos = traducir_error_lista("productos")
    
    


class ProductoInventario(BaseModel):
    id_product: int
    nombre: str
    categoria: str
    total_entradas: int
    total_salidas: int
    stock_actual: int
    minimo: int
    ultima_actualizacion: Optional[datetime]


class ReporteInventarioResponse(BaseModel):
    productos: List[ProductoInventario]
    total_productos: int
    total_stock_general: int
