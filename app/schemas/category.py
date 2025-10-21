from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.schemas.api_response import APIResponse
from app.schemas.base import BaseValidatedModel

class CategoryBase(BaseValidatedModel):
    name: Annotated[str, ...]

    @field_validator("name")
    def validar_nombre(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El nombre de la categoría no puede estar vacío.")
        if len(v) < 3:
            raise ValueError("El nombre de la categoría debe tener al menos 3 caracteres.")
        if len(v) > 100:
            raise ValueError("El nombre de la categoría no puede exceder 100 caracteres.")
        return v

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(BaseValidatedModel):
    id: int
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CategoryPaginationRequest(BaseValidatedModel):
    page: int = 1
    per_page: int = 10

class CategoryUpdateRequest(BaseValidatedModel):
    current_name: str = Field(..., description="Nombre actual de la categoría")
    new_name: str = Field(..., description="Nuevo nombre para la categoría")

class CategorySingleResponse(APIResponse[CategoryResponse]):
    pass
