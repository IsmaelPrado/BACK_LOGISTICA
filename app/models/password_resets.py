from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from app.db.database import Base

class PasswordReset(Base):
    __tablename__ = "password_resets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    reset_token = Column(String(64), nullable=True)  # Token seguro para link
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
