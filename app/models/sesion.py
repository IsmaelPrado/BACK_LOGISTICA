from sqlalchemy import Column, Integer, Numeric, DateTime, Interval, String, ForeignKey, func, text
from app.db.database import Base

class Sesion(Base):
    __tablename__ = "sesiones"

    id = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(
        Integer,
        ForeignKey("usuarios.id_usuario", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    fecha_inicio = Column(DateTime, server_default=func.now(), nullable=False)
    ultima_actividad = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    expiracion_inactividad = Column(
        Interval,
        server_default=text("INTERVAL '5 minutes'"),
        nullable=False
    )
    estado = Column(String(20), nullable=False, server_default="activa")
    latitud = Column(Numeric(9, 6), nullable=True)
    longitud = Column(Numeric(9, 6), nullable=True)
