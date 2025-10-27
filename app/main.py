from fastapi import FastAPI
from app.api.v1 import routes_admin_user, routes_sales
from app.api.v1 import routes_auth
from app.api.v1 import routes_category
from app.api.v1 import routes_product
from app.api.v1 import routes_historial_acciones
from app.api.v1 import routes_purchase 
from app.db.init_db import init_db
from contextlib import asynccontextmanager
from app.db.seed_data import seed_roles_and_permissions
from app.jobs.expirar_sesiones import iniciar_scheduler
from app.middleware.logging import LoggingMiddleware
from app.core.limiter import limiter
from app.core.exception_handlers import register_exception_handlers
from app.middleware.security import basic_auth_middleware 
from app.db.database import async_session



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

# Confirguración de logs
app.add_middleware(LoggingMiddleware)

# Configuración de limitador de velocidad
app.state.limiter = limiter

# Configuración de manejadores de excepciones
register_exception_handlers(app)

@app.get("/")
def root():
    return {"message": "API en funcionamiento"}

app.include_router(routes_auth.router)
app.include_router(routes_admin_user.router)
app.include_router(routes_category.router)
app.include_router(routes_product.router)
app.include_router(routes_sales.router)
app.include_router(routes_historial_acciones.router)
app.include_router(routes_purchase.router)


