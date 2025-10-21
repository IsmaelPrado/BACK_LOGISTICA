from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from app.db.database import Base

from sqlalchemy.orm import relationship

class Purchase(Base):
    __tablename__ = "purchases"

    id_purchase = Column(Integer, primary_key=True, index=True)
    id_user = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)  # quien registró la compra
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
    supplier_name = Column(String(100), nullable=True)

    items = relationship("PurchaseItem", back_populates="purchase", cascade="all, delete-orphan")


