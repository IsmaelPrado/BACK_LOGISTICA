from fastapi import FastAPI
from app.api.v1 import routes_auth
from app.db.init_db import init_db
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializar la base de datos al iniciar la aplicación
    await init_db()
    yield
    
    print("App cerrada")

app = FastAPI(
    title="API",
    description="Backend con FastAPI y PostgreSQL",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
def root():
    return {"message": "API en funcionamiento"}

app.include_router(routes_auth.router)
