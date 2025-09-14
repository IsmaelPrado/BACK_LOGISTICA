from pydantic import BaseModel

class UsuarioCreate(BaseModel):
    nombre_usuario: str
    correo_electronico: str
    contrasena: str
    confirmar_contrasena: str
    rol: str = "usuario"

class UsuarioResponse(BaseModel):
    id_usuario: int
    nombre_usuario: str
    correo_electronico: str
    rol: str
