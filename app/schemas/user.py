from typing import Annotated
from pydantic import BaseModel, Field, EmailStr

class UsuarioCreate(BaseModel):
    nombre_usuario: Annotated[str, Field(min_length=3, max_length=50)]
    correo_electronico: EmailStr
    contrasena: Annotated[str, Field(min_length=8)]
    confirmar_contrasena: str
    rol: str = "usuario"
