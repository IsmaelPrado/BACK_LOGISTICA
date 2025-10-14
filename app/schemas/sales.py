from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

# -----------------------------
# Request
# -----------------------------
class SaleCreateRequest(BaseModel):
    product_name: str = Field(..., description="Nombre del producto a vender")
    quantity: int = Field(..., gt=0, description="Cantidad a vender, debe ser mayor a 0")
    customer_name: Optional[str] = Field(None, description="Nombre del cliente (opcional)")

# -----------------------------
# Response
# -----------------------------
class SaleCreateResponse(BaseModel):
    sale_id: int
    product: str
    quantity: int
    total: float
    previous_inventory: int
    new_inventory: int
    date: datetime

    class Config:
        orm_mode = True
