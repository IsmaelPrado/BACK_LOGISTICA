import re
from pydantic import field_validator

from app.core.enums.roles_enum import UserRole

EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$")

def validar_correo_electronico():
    @field_validator("correo_electronico")
    def _validador(cls, v: str):
        if not EMAIL_REGEX.match(v):
            raise ValueError("El correo electrónico no es válido. Debe tener un formato como 'usuario@dominio.com'.")
        return v
    return _validador


def validar_email():
    @field_validator("email")
    def _validador(cls, v: str):
        if not EMAIL_REGEX.match(v):
            raise ValueError("El correo electrónico no es válido. Debe tener un formato como 'usuario@dominio.com'.")
        return v
    return _validador

def validar_no_vacio(campo: str, min_len: int = None, max_len: int = None):
    """
    Valida que un campo no esté vacío y, opcionalmente, cumpla con una longitud mínima y máxima.
    """
    @field_validator(campo)
    def _validador(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError(f"El campo '{campo}' no puede estar vacío.")
        v = v.strip()

        if min_len is not None and len(v) < min_len:
            raise ValueError(f"El campo '{campo}' debe tener al menos {min_len} caracteres.")
        if max_len is not None and len(v) > max_len:
            raise ValueError(f"El campo '{campo}' no puede tener más de {max_len} caracteres.")

        return v
    return _validador

def validar_contrasena():
    @field_validator("contrasena")
    def _validar_contrasena(cls, v: str):
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
    return _validar_contrasena

def validar_rol():
    @field_validator("rol")
    def _validar_rol(cls, v:str):
        v = v.strip().lower()
        if v not in {UserRole.ADMIN, UserRole.USER}:
            raise ValueError("El rol solo puede ser 'admin' o 'usuario'.")
        return v
    return _validar_rol


