import re
from pydantic import field_validator

from app.core.enums.roles_enum import UserRole

EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$")

INVALID_STRINGS = {"string", "null", "none", "", "undefined"}

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

def validate_strings_recursively(data, parent_key=""):
    if isinstance(data, str):
        if data.strip().lower() in INVALID_STRINGS:  # <- trim aquí
            raise ValueError(f"El campo '{parent_key}' contiene un valor inválido: '{data}'")
    elif isinstance(data, list):
        for i, item in enumerate(data):
            validate_strings_recursively(item, f"{parent_key}[{i}]")
    elif isinstance(data, dict):
        for key, value in data.items():
            new_key = f"{parent_key}.{key}" if parent_key else key
            validate_strings_recursively(value, new_key)

def validar_positivo(campo: str):
    """
    Valida que un campo numérico sea mayor a 0.
    Se puede usar para 'quantity', 'price', etc.
    """
    @field_validator(campo)
    def _validador(cls, v):
        if v <= 0:
            raise ValueError(f"El campo '{campo}' debe ser mayor a 0")
        return v
    return _validador

def validar_lista_minima(campo: str, min_items: int = 1):
    """
    Valida que una lista tenga al menos 'min_items' elementos.
    """
    @field_validator(campo)
    def _validador(cls, v):
        if not isinstance(v, list):
            raise ValueError(f"El campo '{campo}' debe ser una lista")
        if len(v) < min_items:
            raise ValueError(f"El campo '{campo}' debe contener al menos {min_items} elemento(s)")
        return v
    return _validador

def validar_tipo_inventario():
    @field_validator("tipo_inventario", mode="before")
    def _validador(cls, v):
        valores_validos = {"bajo", "bueno", "todos"}
        if isinstance(v, str):
            v = v.lower()
            if v not in valores_validos:
                raise ValueError("El campo 'tipo_inventario' debe ser 'bajo', 'bueno' o 'todos'.")
        return v
    return _validador

def traducir_error_lista(campo: str):
    """
    Traduce el error por defecto de Pydantic cuando un campo no es una lista válida.
    Si el valor no es lista ni None, lanza un mensaje en español.
    """
    @field_validator(campo, mode="before")
    def _validador(cls, v):
        if v is None:
            return v
        if not isinstance(v, list):
            raise ValueError(f"El campo '{campo}' debe ser una lista válida (por ejemplo: ['item1', 'item2']).")
        return v
    return _validador
