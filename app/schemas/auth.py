from pydantic import BaseModel, EmailStr, field_validator
from typing import Annotated
import re

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

# Login con Google OAuth
class GoogleUser(BaseModel):
    id: str
    email: EmailStr
    name: str | None = None
    picture: str | None = None

class GoogleAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: GoogleUser


# REGISTRO USUARIO
class UsuarioRequest(BaseModel):
    nombre_usuario: Annotated[str, ...]  # TODO: agregar validaciones si es necesario
    correo_electronico: str
    contrasena: Annotated[str, ...]
    confirmar_contrasena: str
    rol: str = "usuario"
    
    @field_validator("correo_electronico")
    def validar_email(cls, v):
        pattern = re.compile(r"^[^@]+@[^@]+\.[^@]+$")
        if not pattern.match(v):
            raise ValueError("El correo electrónico no es válido.")
        return v
    
    @field_validator("nombre_usuario")
    def nombre_no_vacio(cls, v):
        if not v or not v.strip():
            raise ValueError("El nombre de usuario no puede estar vacío.")
        if len(v.strip()) < 3:
            raise ValueError("El nombre de usuario debe tener al menos 3 caracteres.")
        return v.strip()

    @field_validator("contrasena")
    def validar_contrasena(cls, v):
        import re
        pattern = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).+$')
        if not pattern.match(v):
            raise ValueError(
                "La contraseña debe contener mayúscula, minúscula, número y carácter especial."
            )
        return v
    
    @field_validator("rol")
    def rol_no_vacio(cls, v):
        if not v or not v.strip():
            raise ValueError("El rol no puede estar vacío.")
        return v.strip()

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

# RECUPERAR CONTRASEÑA
class PasswordRecoveryRequest(BaseModel):
    username: str


class PasswordResetRequest(BaseModel):
    token: str
    new_password: Annotated[str, ...]
    confirm_new_password: str

