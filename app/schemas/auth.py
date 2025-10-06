from datetime import datetime
from fastapi import HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator, model_validator
from typing import Annotated, Optional
import re
from enum import Enum
from app.validators.common_validators import validar_email, validar_correo_electronico, validar_no_vacio

# LOGIN

class LoginType(str, Enum):
    email = "email"
    totp = "totp"
class LoginRequest(BaseModel):
    username: Annotated[str, ...]  
    password: Annotated[str, ...]
    login_type: LoginType

    _validar_username = validar_no_vacio("username")
    _validar_password = validar_no_vacio("password")

    # Validador para traducir mensaje
    @model_validator(mode="before")
    def validar_tipo_login(cls, values: dict) -> dict:
        tipo = values.get("login_type")
        if tipo not in LoginType._value2member_map_:
            raise ValueError("El tipo de login debe ser 'email' o 'totp'")
        return values
class LoginResponse(BaseModel):
    qr_base64: str | None = None

class OTPRequest(BaseModel):
    username: str
    otp: str

    _validar_otp = validar_no_vacio("otp")
    _validar_username = validar_no_vacio("username")


class SessionResponse(BaseModel):
    session_id: int
    fecha_inicio: datetime
    estado: bool
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    tiempo_restante: Optional[int] = None
    token: str

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
    nombre_usuario: Annotated[str, ...]
    correo_electronico: str
    contrasena: Annotated[str, ...]
    confirmar_contrasena: str
    
    rol: str = "usuario"
    
    _validar_email = validar_correo_electronico()
    
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

    _validar_email = validar_email()

# RECUPERAR CONTRASEÑA
class PasswordRecoveryRequest(BaseModel):
    username: str

    _validar_username = validar_no_vacio("username")


class PasswordResetRequest(BaseModel):
    token: str
    new_password: Annotated[str, ...]
    confirm_new_password: str

    _token = validar_no_vacio("token")
    _validar_new_password = validar_no_vacio("new_password")
    _validar_confirm_new_password = validar_no_vacio("confirm_new_password")
