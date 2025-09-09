from fastapi import FastAPI
from app.db.database import engine, Base

app = FastAPI(
    title="API",
    description="Backend con FastAPI y PostgreSQL",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"message": "API en funcionamiento"}
