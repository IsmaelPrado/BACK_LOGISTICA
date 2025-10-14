from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship  
from app.db.database import Base
from app.core.enums.tipo_movimiento import MovementType


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    __table_args = (
        Index("ix_inventory_movements_product_date", "id_product", "date"),
    )
    

    id_movement = Column(Integer, primary_key=True, index=True)
    id_product = Column(Integer, ForeignKey("products.id_product", ondelete="CASCADE"), nullable=False)
    movement_type = Column(SQLEnum(MovementType), nullable=False)  # "entrada" | "salida"
    quantity = Column(Integer, nullable=False)
    reason = Column(String(100), nullable=True)  # "compra", "venta", "ajuste", etc.
    related_id = Column(Integer, nullable=True)  # ID de venta o compra opcional
    previous_inventory = Column(Integer, nullable=False)
    new_inventory = Column(Integer, nullable=False)
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_id = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=True)

    product = relationship("Product", back_populates="inventory_movements")
