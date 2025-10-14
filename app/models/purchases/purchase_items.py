from sqlalchemy import Column, ForeignKey, Integer, Numeric
from app.db.database import Base
from sqlalchemy.orm import relationship

class PurchaseItem(Base):
    __tablename__ = "purchase_items"

    id_purchase_item = Column(Integer, primary_key=True, index=True)
    id_purchase = Column(Integer, ForeignKey("purchases.id_purchase", ondelete="CASCADE"), nullable=False)
    id_product = Column(Integer, ForeignKey("products.id_product"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)  # costo unitario

    purchase = relationship("Purchase", back_populates="items")
    product = relationship("Product")
