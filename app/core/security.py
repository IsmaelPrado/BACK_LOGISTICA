from datetime import datetime, timedelta
import secrets
from fastapi import Request
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "sub": data.get("sub")})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

from typing import Optional, Dict, Any

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
    
def generate_state():
    return secrets.token_urlsafe(16)

def get_client_ip(request: Request) -> str:
    """
    Intenta obtener la IP pública real del cliente:
    1) X-Forwarded-For (first)
    2) X-Real-IP
    3) request.client.host
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # si hay una lista, la primera es la IP original del cliente
        return forwarded.split(",")[0].strip()
    xr = request.headers.get("X-Real-IP")
    if xr:
        return xr.strip()
    # fallback
    client = request.client
    if client:
        return client.host
    return ""
    