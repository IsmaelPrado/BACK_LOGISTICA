from sqlalchemy import Column, Integer, String
from app.db.database import Base
from app.models.associations.rol_permisos import rol_permisos
from sqlalchemy.orm import relationship

class Rol(Base):
    __tablename__ = "roles"
    id_rol = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(String(255))

    permisos = relationship(
        "Permiso",
        secondary=rol_permisos,
        back_populates="roles"
    )
