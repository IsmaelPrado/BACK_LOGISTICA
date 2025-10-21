from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.schemas.api_response import APIResponse
from app.schemas.base import BaseValidatedModel

class ProductBase(BaseValidatedModel):
    code: str = Field(..., max_length=50)
    barcode: Optional[str] = Field(None, max_length=100)
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    sale_price: float
    inventory: int
    min_inventory: int
    category: str

    @field_validator("name")
    def validar_nombre(cls, v):
        if not v.strip():
            raise ValueError("El nombre del producto no puede estar vacío.")
        if len(v.strip()) < 3:
            raise ValueError("El nombre debe tener al menos 3 caracteres.")
        return v.strip()

    @field_validator("sale_price")
    def validar_precio(cls, v):
        if v <= 0:
            raise ValueError("El precio debe ser mayor que cero.")
        return v

    @field_validator("inventory")
    def validar_inventario(cls, v):
        if v < 0:
            raise ValueError("El inventario no puede ser negativo.")
        return v

    @field_validator("min_inventory")
    def validar_inventario_minimo(cls, v):
        if v < 0:
            raise ValueError("El inventario mínimo no puede ser negativo.")
        return v


class ProductCreate(BaseValidatedModel):
    """Schema para crear un producto — excluye campos automáticos."""
    pass


class ProductResponse(BaseValidatedModel):
    id_product: int
    code: str
    barcode: Optional[str]
    name: str
    description: Optional[str]
    sale_price: float
    inventory: int
    min_inventory: int
    category: str
    date_added: datetime  # Se mostrará, pero no se envía al crear

    model_config = ConfigDict(from_attributes=True)

class ProductPaginationRequest(BaseValidatedModel):
    page: int = 1
    per_page: int = 10
    category_name: Optional[str] = None  # filtro por nombre de categoría
    product_name: Optional[str] = None   # búsqueda por palabra clave en nombre de producto

class ProductDeleteRequest(BaseValidatedModel):
    """Datos necesarios para eliminar un producto por su nombre."""
    name: str = Field(..., min_length=1, description="Nombre del producto a eliminar")

class ProductUpdateRequest(BaseValidatedModel):
    current_name: str = Field(..., description="Nombre actual del producto a actualizar")
    new_name: Optional[str] = Field(None, max_length=100, description="Nuevo nombre del producto")
    barcode: Optional[str] = Field(None, max_length=100, description="Nuevo código de barras")
    description: Optional[str] = Field(None, description="Nueva descripción del producto")
    sale_price: Optional[float] = Field(None, description="Nuevo precio de venta")
    inventory: Optional[int] = Field(None, description="Nuevo inventario")
    min_inventory: Optional[int] = Field(None, description="Nuevo inventario mínimo")
    id_category: Optional[int] = Field(None, description="Nueva categoría del producto")


class ProductSingleResponse(APIResponse[ProductResponse]):
    pass
