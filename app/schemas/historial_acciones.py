from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

# --- Schema para un item del historial ---
class HistorialAccionItem(BaseModel):
    id_historial: int
    id_usuario: int
    nombre_usuario: str
    accion: str
    modulo: str
    descripcion: Optional[str] = None
    datos_anteriores: Optional[dict] = None
    datos_nuevos: Optional[dict] = None
    fecha_accion: datetime

    class Config:
        orm_mode = True

# --- Schema para request de filtros y paginación ---
class HistorialAccionQuery(BaseModel):
    page: int = 1
    per_page: int = 10
    usuario_nombre: Optional[str] = None
    accion: Optional[str] = None
    modulo: Optional[str] = None
    fecha_inicio: Optional[str] = None
    fecha_fin: Optional[str] = None
