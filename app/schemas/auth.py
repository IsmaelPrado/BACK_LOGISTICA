from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator, model_validator
from typing import Annotated, Optional
from enum import Enum
from app.schemas.base import BaseValidatedModel
from app.validators.common_validators import validar_email, validar_correo_electronico, validar_no_vacio, validar_contrasena, validar_rol
from app.core.enums.roles_enum import UserRole

# LOGIN

class LoginType(str, Enum):
    email = "email"
    totp = "totp"
class LoginRequest(BaseValidatedModel):
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
class LoginResponse(BaseValidatedModel):
    qr_base64: str | None = None

class OTPRequest(BaseValidatedModel):
    username: str
    otp: str

    _validar_otp = validar_no_vacio("otp")
    _validar_username = validar_no_vacio("username")


class SessionResponse(BaseValidatedModel):
    session_id: int
    fecha_inicio: datetime
    estado: bool
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    tiempo_restante: Optional[int] = None
    token: str

# Login con Google OAuth
class GoogleUser(BaseValidatedModel):
    id: str
    email: EmailStr
    name: str | None = None
    picture: str | None = None

class GoogleAuthResponse(BaseValidatedModel):
    access_token: str
    token_type: str = "bearer"
    user: GoogleUser


# REGISTRO USUARIO
class UsuarioRequest(BaseValidatedModel):
    nombre_usuario: Annotated[str, ...]
    correo_electronico: str
    contrasena: Annotated[str, ...]
    confirmar_contrasena: str
    
    rol: str = UserRole.USER
    
    _validar_email = validar_correo_electronico()
    
    _validar_nombre_usuario = validar_no_vacio("nombre_usuario")

    _validar_contrasena = validar_contrasena()
    
    _validar_rol = validar_rol()


    @field_validator("confirmar_contrasena")
    def contrasenas_coinciden(cls, v, values):
        if "contrasena" in values.data and v != values.data["contrasena"]:
            raise ValueError("Las contraseñas no coinciden")
        return v


class UsuarioResponse(BaseValidatedModel):
    id_usuario: int
    nombre_usuario: str
    correo_electronico: EmailStr
    rol: str

# RECUPERAR USUARIO
class UsernameRecoveryRequest(BaseValidatedModel):
    email: str

    _validar_email = validar_email()

# RECUPERAR CONTRASEÑA
class PasswordRecoveryRequest(BaseValidatedModel):
    username: str

    _validar_username = validar_no_vacio("username")


class PasswordResetRequest(BaseValidatedModel):
    token: str
    new_password: Annotated[str, ...]
    confirm_new_password: str

    _token = validar_no_vacio("token")
    _validar_new_password = validar_no_vacio("new_password")
    _validar_confirm_new_password = validar_no_vacio("confirm_new_password")
