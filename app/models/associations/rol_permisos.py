from sqlalchemy import Table, Column, Integer, ForeignKey
from app.db.database import Base

rol_permisos = Table(
    "rol_permisos",
    Base.metadata,
    Column("id_rol", Integer, ForeignKey("roles.id_rol", ondelete="CASCADE"), primary_key=True),
    Column("id_permiso", Integer, ForeignKey("permisos.id_permiso", ondelete="CASCADE"), primary_key=True)
)
