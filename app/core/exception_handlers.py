# app/core/exception_handlers.py
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import status
from slowapi.errors import RateLimitExceeded

async def validation_exception_handler(request, exc: RequestValidationError):
    # Si el error viene por JSON mal formado
    if "JSON decode error" in str(exc):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "El cuerpo enviado no es un JSON válido"}
        )
        
    first_error = exc.errors()[0]["msg"] if exc.errors() else "Error de validación"
    
     # ✅ Solo este caso específico
    if first_error == "Input should be a valid string":
        first_error = "Envía los datos siguiendo el tipo que espera cada campo del JSON."


    # Quitar prefijo automático de Pydantic
    if first_error.lower().startswith("value error,"):
        first_error = first_error.split(",", 1)[1].strip()

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": first_error},
    )


async def rate_limit_handler(request, exc: RateLimitExceeded):
    # Mensaje personalizado
    custom_message = "Has superado el límite de intentos. Intenta nuevamente más tarde."
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": custom_message}
    )