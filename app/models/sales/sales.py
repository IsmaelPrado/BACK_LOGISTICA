from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, ForeignKey, Numeric, String
from sqlalchemy.orm import relationship
from app.db.database import Base

class Sale(Base):
    __tablename__ = "sales"

    id_sale = Column(Integer, primary_key=True, index=True)
    id_user = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)  # quien realizó la venta
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
    customer_name = Column(String(100), nullable=True)

    # Relación con detalles de la venta
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
