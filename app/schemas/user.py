from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# -----------------------------
# Request para crear usuario
# -----------------------------
class UsuarioCreateRequest(BaseModel):
    nombre_usuario: str = Field(..., min_length=3, max_length=50)
    correo_electronico: EmailStr
    contrasena: str = Field(..., min_length=6, max_length=128)
    rol: Optional[str] = "usuario"  # rol por defecto
    permisos: Optional[List[str]] = []  # Nombres de permisos

class UsuarioCreateResponse(BaseModel):
    id_usuario: int
    nombre_usuario: str
    correo_electronico: EmailStr
    rol: str
    secret_2fa: Optional[str] = None
    permisos: List[str] = []
    fecha_creacion: datetime

    class Config:
        orm_mode = True
