from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.database import Base

class Product(Base):
    __tablename__ = "products"

    id_product = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), nullable=False, unique=True)
    barcode = Column(String(100), nullable=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    sale_price = Column(Numeric(10, 2), nullable=False)
    inventory = Column(Integer, nullable=False, default=0)
    min_inventory = Column(Integer, nullable=False, default=0)

    # 🔹 Mantén el ondelete="RESTRICT" para que la BD no deje eliminar si hay productos asociados
    id_category = Column(Integer, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)

    # 🔹 Usa server_default para que se genere automáticamente desde el servidor
    date_added = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 🔹 Relación bidireccional con Category
    category = relationship("Category", back_populates="products")
