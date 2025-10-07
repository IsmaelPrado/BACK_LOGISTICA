import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import secrets
from fastapi import Request
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

async def hash_password_async(password: str) -> str:
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        # Ejecuta la función de hashing en un hilo separado
        hashed = await loop.run_in_executor(pool, hash_password, password)
    return hashed

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_session_token() -> str:
    return secrets.token_urlsafe(64)
    
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
    