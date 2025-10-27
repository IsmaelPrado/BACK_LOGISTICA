from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List

from app.schemas.base import BaseValidatedModel
from app.validators.common_validators import validar_lista_minima, validar_positivo

# -----------------------------
# Request
# -----------------------------
class SaleProductRequest(BaseValidatedModel):
    product_name: str = Field(..., description="Nombre del producto a vender")
    quantity: int = Field(..., description="Cantidad a vender, debe ser mayor a 0")
    _validar_quantity = validar_positivo("quantity")

class SaleCreateRequest(BaseModel):
    products: List[SaleProductRequest] = Field(..., description="Lista de productos a vender")
    customer_name: Optional[str] = Field(None, description="Nombre del cliente (opcional)")
    _validar_products = validar_lista_minima("products", min_items=1)


# -----------------------------
# Response
# -----------------------------
class SaleProductResponse(BaseValidatedModel):
    product: str
    quantity: int
    price: float
    previous_inventory: int
    new_inventory: int
    min_inventory: int

class SaleCreateResponse(BaseValidatedModel):
    sale_id: int
    total: float
    date: datetime
    customer_name: Optional[str]
    products: List[SaleProductResponse]
    low_stock_products: Optional[List[dict]] = []  # Lista de productos que quedaron bajo inventario mínimo

    class Config:
        orm_mode = True


