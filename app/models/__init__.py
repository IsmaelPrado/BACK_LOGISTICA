# app/models/__init__.py
from app.db.database import Base

# Importar modelos
from app.models.rol import Rol
from app.models.permiso import Permiso
from app.models.user import Usuario
from app.models.historial_acciones import HistorialAccion

# Importar tablas de asociación (no clases)
from app.models.associations.usuario_permisos import usuario_permisos
from app.models.associations.rol_permisos import rol_permisos

__all__ = [
    "Base",
    "Usuario",
    "Rol",
    "Permiso",
    "usuario_permisos",
    "rol_permisos",
]
