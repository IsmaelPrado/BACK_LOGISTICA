from sqlalchemy import Table, Column, Integer, ForeignKey
from app.db.database import Base

usuario_permisos = Table(
    "usuario_permisos",
    Base.metadata,
    Column("id_usuario", Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), primary_key=True),
    Column("id_permiso", Integer, ForeignKey("permisos.id_permiso", ondelete="CASCADE"), primary_key=True)
)
