from datetime import datetime
from pydantic import Field
from typing import Optional, List
from app.schemas.base import BaseValidatedModel
from app.validators.common_validators import validar_lista_minima, validar_positivo

# -----------------------------
# Request
# -----------------------------
class PurchaseProductRequest(BaseValidatedModel):
    product_name: str = Field(..., description="Nombre del producto a comprar")
    quantity: int = Field(..., description="Cantidad a comprar, debe ser mayor a 0")
    price: float = Field(..., description="Costo unitario del producto")
    _validar_quantity = validar_positivo("quantity")
    _validar_price = validar_positivo("price")
    
class PurchaseCreateRequest(BaseValidatedModel):
    products: List[PurchaseProductRequest] = Field(..., description="Lista de productos a comprar")
    supplier_name: Optional[str] = Field(None, description="Nombre del proveedor (opcional)")
    _validar_products = validar_lista_minima("products", min_items=1)

# -----------------------------
# Response
# -----------------------------
class PurchaseProductResponse(BaseValidatedModel):
    product: str
    quantity: int
    price: float
    previous_inventory: int
    new_inventory: int

class PurchaseCreateResponse(BaseValidatedModel):
    purchase_id: int
    total: float
    date: datetime
    supplier_name: Optional[str]
    products: List[PurchaseProductResponse]

    class Config:
        orm_mode = True
