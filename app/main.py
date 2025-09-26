from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from app.api.v1 import routes_auth
from app.db.init_db import init_db
from contextlib import asynccontextmanager
from app.jobs.expirar_sesiones import iniciar_scheduler
from app.middleware.logging import LoggingMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from app.core.limiter import limiter
from app.core.exception_handlers import validation_exception_handler, rate_limit_handler
from app.middleware.security import basic_auth_middleware 

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializar la base de datos al iniciar la aplicación
    await init_db()
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
