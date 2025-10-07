from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.api.v1 import routes_admin_user
from app.api.v1 import routes_auth
from app.api.v1 import routes_category
from app.db.init_db import init_db
from contextlib import asynccontextmanager
from app.db.seed_data import seed_roles_and_permissions
from app.dependencies.auth import AdminSessionError
from app.jobs.expirar_sesiones import iniciar_scheduler
from app.middleware.logging import LoggingMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from app.core.limiter import limiter
from app.core.exception_handlers import validation_exception_handler, rate_limit_handler
from app.middleware.security import basic_auth_middleware 
from app.db.database import async_session
from app.schemas.api_response import APIResponse
from app.core.responses import ResponseCode


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializar la base de datos al iniciar la aplicación
    await init_db()

    # Sembrar datos iniciales
    async with async_session() as session:
        await seed_roles_and_permissions(session)

    # Iniciar el scheduler para tareas periódicas
    iniciar_scheduler()
    yield
    
    print("App cerrada")

app = FastAPI(
    title="API",
    description="Backend con FastAPI y PostgreSQL",
    version="1.0.0",
    lifespan=lifespan
)

app.middleware("http")(basic_auth_middleware)

# Configuración de manejadores de excepciones
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Confirguración de logs
app.add_middleware(LoggingMiddleware)

# Configuración de limitador de velocidad
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

@app.get("/")
def root():
    return {"message": "API en funcionamiento"}

app.include_router(routes_auth.router)
app.include_router(routes_admin_user.router)
app.include_router(routes_category.router)

@app.exception_handler(AdminSessionError)
async def admin_session_exception_handler(request: Request, exc: AdminSessionError):
    return JSONResponse(
        status_code=401,
        content=APIResponse.from_enum(
            ResponseCode.INVALID_TOKEN,
            detail=exc.detail
        ).dict()
    )

@app.exception_handler(ValueError)
async def value_error_exception_handler(request: Request, exc: ValueError):
    """
    Maneja todos los ValueError lanzados en la aplicación y devuelve un APIResponse
    consistente con ResponseCode.BAD_REQUEST.
    """
    return JSONResponse(
        status_code=400,
        content=APIResponse.from_enum(
            ResponseCode.BAD_REQUEST,
            detail=str(exc)
        ).dict()
    )

