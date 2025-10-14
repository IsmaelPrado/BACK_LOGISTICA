from sqlalchemy import Column, ForeignKey, Integer, Numeric

from app.db.database import Base
from sqlalchemy.orm import relationship

class SaleItem(Base):
    __tablename__ = "sale_items"

    id_sale_item = Column(Integer, primary_key=True, index=True)
    id_sale = Column(Integer, ForeignKey("sales.id_sale", ondelete="CASCADE"), nullable=False)
    id_product = Column(Integer, ForeignKey("products.id_product"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)  # precio unitario

    sale = relationship("Sale", back_populates="items")
    product = relationship("Product")
