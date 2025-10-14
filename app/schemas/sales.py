from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List

# -----------------------------
# Request
# -----------------------------
class SaleProductRequest(BaseModel):
    product_name: str = Field(..., description="Nombre del producto a vender")
    quantity: int = Field(..., gt=0, description="Cantidad a vender, debe ser mayor a 0")

class SaleCreateRequest(BaseModel):
    products: List[SaleProductRequest] = Field(..., min_items=1, description="Lista de productos a vender")
    customer_name: Optional[str] = Field(None, description="Nombre del cliente (opcional)")


# -----------------------------
# Response
# -----------------------------
class SaleProductResponse(BaseModel):
    product: str
    quantity: int
    price: float
    previous_inventory: int
    new_inventory: int
    min_inventory: int

class SaleCreateResponse(BaseModel):
    sale_id: int
    total: float
    date: datetime
    customer_name: Optional[str]
    products: List[SaleProductResponse]

    class Config:
        orm_mode = True


