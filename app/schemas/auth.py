from fastapi import HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator, model_validator
from typing import Annotated
import re
from enum import Enum

# LOGIN

class LoginType(str, Enum):
    email = "email"
    totp = "totp"
class LoginRequest(BaseModel):
    username: Annotated[str, ...]  # TODO: agregar validaciones si es necesario
    password: Annotated[str, ...]
    login_type: LoginType

    # Validador para traducir mensaje
    @model_validator(mode="before")
    def validar_tipo_login(cls, values: dict) -> dict:
        tipo = values.get("login_type")
        if tipo not in LoginType._value2member_map_:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El tipo de login debe ser 'email' o 'totp'"
            )
        return values
class LoginResponse(BaseModel):
    detail:str
    qr_base64: str | None = None

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
        # Validar longitud
        if len(v) < 5:
            raise ValueError("La contraseña debe tener al menos 5 caracteres.")
        if len(v) > 64:
            raise ValueError("La contraseña no puede exceder 64 caracteres.")
        
        # Validar composición
        pattern = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).+$')
        if not pattern.match(v):
            raise ValueError(
                "La contraseña debe contener mayúscula, minúscula, número y carácter especial."
            )
        return v
    
    @field_validator("rol")
    def rol_valido(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in {"admin", "usuario"}:
            raise ValueError("El rol solo puede ser 'admin' o 'usuario'.")
        return v


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
    email: str

    @field_validator("email")
    def email_valido(cls, v):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", v):
            raise ValueError("El correo electrónico no es válido. Debe tener un formato como 'usuario@dominio.com'.")
        return v

# RECUPERAR CONTRASEÑA
class PasswordRecoveryRequest(BaseModel):
    username: str


class PasswordResetRequest(BaseModel):
    token: str
    new_password: Annotated[str, ...]
    confirm_new_password: str

