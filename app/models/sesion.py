from datetime import timedelta
from sqlalchemy import Column, Integer, Numeric, DateTime, Interval, Boolean, ForeignKey, String, func, text
from app.db.database import Base
from app.core.config import settings

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
        default=lambda: timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        nullable=False
    )
    estado = Column(Boolean, nullable=False, server_default=text("TRUE"))
    latitud = Column(Numeric(9, 6), nullable=True)
    longitud = Column(Numeric(9, 6), nullable=True)
    token = Column(String, unique=True, nullable=False, index=True)
