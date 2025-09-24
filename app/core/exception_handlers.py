# app/core/exception_handlers.py
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import status
from slowapi.errors import RateLimitExceeded
from app.schemas.api_response import APIResponse
from fastapi.responses import JSONResponse
from fastapi import status, Request
from fastapi.exceptions import RequestValidationError
from app.core.responses import ResponseCode
from app.schemas.api_response import APIResponse
import logging

logger = logging.getLogger(__name__)

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Error de validación en {request.url}: {exc.errors()}")

    # Si el error viene por JSON mal formado
    if "JSON decode error" in str(exc):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=APIResponse.from_enum(
                ResponseCode.VALIDATION_ERROR,
                detail="El cuerpo enviado no es un JSON válido"
            ).model_dump()  # convertir BaseModel a dict
        )
    
    first_error = exc.errors()[0]["msg"] if exc.errors() else "Error de validación"

    # Casos específicos de mensaje
    if first_error == "Input should be a valid string":
        first_error = "Tipo de dato inválido"

    # Quitar prefijo automático de Pydantic
    if first_error.lower().startswith("value error,"):
        first_error = first_error.split(",", 1)[1].strip()

    # ✅ Retornar siempre APIResponse
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=APIResponse.from_enum(
            ResponseCode.VALIDATION_ERROR,
            detail=first_error
        ).model_dump()
    )

async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    custom_message = "Has superado el límite de intentos. Intenta nuevamente más tarde."
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=APIResponse.from_enum(
            ResponseCode.RATE_LIMIT_EXCEEDED,
            detail=custom_message
        ).model_dump()
    )