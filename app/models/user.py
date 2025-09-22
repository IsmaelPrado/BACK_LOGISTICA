from sqlalchemy import Column, Integer, String, DateTime, func
from app.db.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario = Column(Integer, primary_key=True, index=True)
    nombre_usuario = Column(String(50), unique=True, nullable=False, index=True)
    correo_electronico = Column(String(100), unique=True, nullable=False, index=True)
    contrasena = Column(String(255), nullable=False)  # hash
    rol = Column(String(20), nullable=False, server_default="usuario")
    secret_2fa = Column(String(64), nullable = True)
    fecha_creacion = Column(DateTime, server_default=func.now(), nullable=False)
