# app/core/exception_handlers.py
import logging
from fastapi import Request, status, FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded

from app.schemas.api_response import APIResponse
from app.core.enums.responses import ResponseCode
from app.dependencies.auth import AdminSessionError, UserSessionError  

logger = logging.getLogger(__name__)

# ==============================
# HANDLERS INDIVIDUALES
# ==============================

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Error de validación en {request.url}: {exc.errors()}")

    if "JSON decode error" in str(exc):
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=APIResponse.from_enum(
                ResponseCode.VALIDATION_ERROR,
                detail="El cuerpo enviado no es un JSON válido"
            ).model_dump()
        )

    first_error = exc.errors()[0]["msg"] if exc.errors() else "Error de validación"

    if first_error == "Input should be a valid string":
        first_error = "Tipo de dato inválido"

    if first_error.lower().startswith("value error,"):
        first_error = first_error.split(",", 1)[1].strip()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=APIResponse.from_enum(
            ResponseCode.VALIDATION_ERROR,
            detail=first_error
        ).model_dump()
    )


async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    custom_message = "Has superado el límite de intentos. Intenta nuevamente más tarde."
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=APIResponse.from_enum(
            ResponseCode.RATE_LIMIT_EXCEEDED,
            detail=custom_message
        ).model_dump()
    )


async def admin_session_exception_handler(request: Request, exc: AdminSessionError):
    """Maneja errores de sesión de administrador."""
    return JSONResponse(
        status_code=401,
        content=APIResponse.from_enum(
            ResponseCode.INVALID_TOKEN,
            detail=exc.detail
        ).model_dump()
    )

async def user_session_exception_handler(request: Request, exc: UserSessionError):
    """Maneja errores de sesión de usuario."""
    return JSONResponse(
        status_code=401,
        content=APIResponse.from_enum(
            ResponseCode.INVALID_TOKEN,
            detail=exc.detail
        ).model_dump()
    )


async def value_error_exception_handler(request: Request, exc: ValueError):
    """Maneja ValueError y devuelve un APIResponse estándar."""
    return JSONResponse(
        status_code=400,
        content=APIResponse.from_enum(
            ResponseCode.BAD_REQUEST,
            detail=str(exc)
        ).model_dump()
    )


# ==============================
# REGISTRO CENTRAL DE HANDLERS
# ==============================

def register_exception_handlers(app: FastAPI):
    """Registra todos los handlers de excepción en la app."""

    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
    app.add_exception_handler(AdminSessionError, admin_session_exception_handler)
    app.add_exception_handler(UserSessionError, user_session_exception_handler)
    app.add_exception_handler(ValueError, value_error_exception_handler)
