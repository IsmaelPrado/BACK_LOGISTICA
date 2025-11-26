# models/ticket_config.py
from sqlalchemy import Column, Integer, BigInteger, String, Text, LargeBinary, DateTime, func
from app.db.database import Base

class TicketConfiguration(Base):
    __tablename__ = "ticket_configurations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, index=True, nullable=False)  # referencia a tu usuario
    name = Column(String(100), nullable=True)  # nombre del perfil (opcional)

    # JSON con todos los parámetros del TicketConfig (shop, columnas, flags, etc.)
    config_json = Column(Text, nullable=False)

    # Logo (opcional) — varbinary / bytea
    logo = Column(LargeBinary, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
