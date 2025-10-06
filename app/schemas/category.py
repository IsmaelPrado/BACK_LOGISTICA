from datetime import datetime
from pydantic import BaseModel, field_validator
from app.schemas.api_response import APIResponse  # Tu respuesta estándar

# ---- Category Schemas ----

class CategoryBase(BaseModel):
    name: str

    @field_validator("name")
    def validar_nombre(cls, v):
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


class CategoryUpdate(BaseModel):
    name: str

    @field_validator("name")
    def validar_nombre(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("El nombre no puede estar vacío.")
        return v


class CategoryResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        orm_mode = True


# ---- API Responses ----

class CategoryListResponse(APIResponse[list[CategoryResponse]]):
    pass


class CategorySingleResponse(APIResponse[CategoryResponse]):
    pass
