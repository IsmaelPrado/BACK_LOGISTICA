from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

from app.validators.common_validators import validar_contrasena, validar_correo_electronico, validar_no_vacio, validar_rol
from app.core.enums.roles_enum import UserRole

# -----------------------------
# Request para crear usuario
# -----------------------------
class UsuarioCreateRequest(BaseModel):
    nombre_usuario: str 
    correo_electronico: str
    contrasena: str 
    rol: Optional[str] = UserRole.USER
    permisos: Optional[List[str]] = []  # Nombres de permisos

    _validar_nombre_usuario = validar_no_vacio("nombre_usuario")
    _validar_correo_electronico = validar_no_vacio("correo_electronico")
    _validar_contrasena = validar_no_vacio("contrasena")
    _validar_rol = validar_no_vacio("rol")

    _validar_contrasena = validar_contrasena()
    
    _validar_rol = validar_rol()

    _validar_email = validar_correo_electronico()


class UsuarioCreateResponse(BaseModel):
    id_usuario: int
    nombre_usuario: str
    correo_electronico: str
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

# -----------------------------
# Request para actualizar usuario
# -----------------------------
class UsuarioUpdateRequest(BaseModel):
    nombre_usuario: str = Field(..., description="Nombre actual del usuario a actualizar")
    nuevo_nombre_usuario: Optional[str] = Field(None, min_length=3, max_length=50)
    correo_electronico: Optional[str] = None
    contrasena: Optional[str] 
    rol: Optional[str] = None
    permisos: Optional[List[str]] = []  # Nombres de permisos

    _validar_nombre_usuario = validar_no_vacio("nombre_usuario")
    _validar_nuevo_nombre_usuario = validar_no_vacio("nuevo_nombre_usuario", min_len=3, max_len=50)
    _validar_correo_electronico = validar_no_vacio("correo_electronico")
    _validar_contrasena = validar_no_vacio("contrasena")
    _validar_rol = validar_no_vacio("rol")

    _validar_rol = validar_rol()
    _validar_contrasena = validar_contrasena()

    _validar_email = validar_correo_electronico()


class UsuarioUpdateResponse(BaseModel):
    id_usuario: int
    nombre_usuario: str
    correo_electronico: EmailStr
    rol: str
    permisos: List[str] = []
    fecha_actualizacion: datetime

    class Config:
        orm_mode = True