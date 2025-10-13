from sqlalchemy import Column, Integer, String, DateTime, func
from app.db.database import Base
from sqlalchemy.orm import relationship  

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    products = relationship("Product", back_populates="category", cascade="all, delete-orphan")
