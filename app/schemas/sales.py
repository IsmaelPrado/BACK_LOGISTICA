from datetime import datetime
from pydantic import BaseModel, Field, model_validator
from typing import Optional, List

from app.schemas.base import BaseValidatedModel
from app.validators.common_validators import validar_lista_minima, validar_positivo

# -----------------------------
# Request
# -----------------------------
class SaleProductRequest(BaseModel):
    product_code: Optional[str] = Field(..., description="Código o código de barras del producto a vender")
    barcode: Optional[str] = None

    quantity: int = Field(..., description="Cantidad a vender, debe ser mayor a 0")

    @model_validator(mode="after")
    def validar_quantity(self):
        if self.quantity <= 0:
            raise ValueError("La cantidad debe ser mayor a 0")
        return self


class SaleCreateRequest(BaseModel):
    products: List[SaleProductRequest] = Field(..., description="Lista de productos a vender")
    customer_name: Optional[str] = Field(None, description="Nombre del cliente (opcional)")

    @model_validator(mode="after")
    def validar_products(self):
        if not self.products or len(self.products) == 0:
            raise ValueError("Debe incluir al menos un producto en la venta")
        return self

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


