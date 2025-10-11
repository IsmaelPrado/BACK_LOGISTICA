from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

from app.validators.common_validators import validar_correo_electronico, validar_no_vacio
from app.core.enums.roles_enum import UserRole

# -----------------------------
# Request para crear usuario
# -----------------------------
class UsuarioCreateRequest(BaseModel):
    nombre_usuario: str = Field(..., min_length=3, max_length=50)
    correo_electronico: EmailStr
    contrasena: str = Field(..., min_length=6, max_length=128)
    rol: Optional[str] = UserRole.USER
    permisos: Optional[List[str]] = []  # Nombres de permisos

    _validar_nombre_usuario = validar_no_vacio("nombre_usuario")
    _validar_correo_electronico = validar_no_vacio("correo_electronico")
    _validar_contrasena = validar_no_vacio("contrasena")
    _validar_rol = validar_no_vacio("rol")

    _validar_email = validar_correo_electronico()


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

# -----------------------------
# Request para eliminar usuario
# -----------------------------
class UsuarioDeleteRequest(BaseModel):
    nombre_usuario: str = Field(...)

    _validar_nombre_usuario = validar_no_vacio("nombre_usuario", min_len=3, max_len=50)