from pydantic import BaseModel, EmailStr, field_validator
from typing import Annotated

# LOGIN
class LoginRequest(BaseModel):
    username: Annotated[str, ...]  # TODO: agregar validaciones si es necesario
    password: Annotated[str, ...]


class DefaultResponse(BaseModel):
    detail: str

class OTPRequest(BaseModel):
    username: str
    otp: str

class OTPResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# REGISTRO USUARIO
class UsuarioRequest(BaseModel):
    nombre_usuario: Annotated[str, ...]  # TODO: agregar validaciones si es necesario
    correo_electronico: EmailStr
    contrasena: Annotated[str, ...]
    confirmar_contrasena: str
    rol: str = "usuario"

    @field_validator("confirmar_contrasena")
    def contrasenas_coinciden(cls, v, values):
        if "contrasena" in values.data and v != values.data["contrasena"]:
            raise ValueError("Las contraseñas no coinciden")
        return v


class UsuarioResponse(BaseModel):
    id_usuario: int
    nombre_usuario: str
    correo_electronico: EmailStr
    rol: str

# RECUPERAR USUARIO
class UsernameRecoveryRequest(BaseModel):
    email: EmailStr