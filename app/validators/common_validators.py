import re
from pydantic import field_validator

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

def validar_no_vacio(campo: str):
    @field_validator(campo)
    def _validador(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError(f"El campo '{campo}' no puede estar vacío.")
        return v.strip()
    return _validador

