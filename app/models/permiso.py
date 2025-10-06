from sqlalchemy import Column, Integer, String
from app.db.database import Base
from sqlalchemy.orm import relationship

class Permiso(Base):
    __tablename__ = "permisos"
    id_permiso = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(String(255))

    usuarios = relationship(
        "Usuario",
        secondary="usuario_permisos",
        back_populates="permisos"
    )
    roles = relationship(
        "Rol",
        secondary="rol_permisos",
        back_populates="permisos"
    )
