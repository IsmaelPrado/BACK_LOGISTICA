from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.db.database import Base  

class HistorialAccion(Base):
    __tablename__ = "historial_acciones"

    id_historial = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    accion = Column(String(50), nullable=False)  # crear, actualizar, eliminar, listar, etc.
    modulo = Column(String(50), nullable=False)  # productos, categorías, ventas, etc.
    descripcion = Column(String(255), nullable=True)  # detalle libre
    datos_anteriores = Column(JSON, nullable=True)  # estado previo (opcional)
    datos_nuevos = Column(JSON, nullable=True)      # estado nuevo (opcional)
    fecha_accion = Column(DateTime, server_default=func.now(), nullable=False)

    usuario = relationship("Usuario", backref="historial_acciones")