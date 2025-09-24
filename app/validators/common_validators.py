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

