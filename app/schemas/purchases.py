from datetime import datetime
from pydantic import Field
from typing import Optional, List
from app.schemas.base import BaseValidatedModel

# -----------------------------
# Request
# -----------------------------
class PurchaseProductRequest(BaseValidatedModel):
    product_name: str = Field(..., description="Nombre del producto a comprar")
    quantity: int = Field(..., gt=0, description="Cantidad a comprar, debe ser mayor a 0")
    price: float = Field(..., gt=0, description="Costo unitario del producto")

class PurchaseCreateRequest(BaseValidatedModel):
    products: List[PurchaseProductRequest] = Field(..., min_items=1, description="Lista de productos a comprar")
    supplier_name: Optional[str] = Field(None, description="Nombre del proveedor (opcional)")

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
