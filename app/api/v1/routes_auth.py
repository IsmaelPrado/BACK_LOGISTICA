from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.user import UsuarioCreate
from app.services.user_service import authenticate_user, create_user
from app.core.security import create_access_token
from app.models.user import Usuario

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=LoginResponse)
async def login(
    login_request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        user: Usuario = await authenticate_user(db, login_request.username, login_request.password)
    except ValueError as e:
        # Mensaje claro según el error
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    
    access_token = create_access_token(data={"sub": user.nombre_usuario, "rol": user.rol})

    return LoginResponse(access_token=access_token)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: UsuarioCreate, db: AsyncSession = Depends(get_db)):
    try:
        nuevo = await create_user(db, user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)  # Aquí siempre sale {"detail": "mensaje"}
        )

    return {
        "mensaje": "Usuario creado con éxito",
        "usuario": {
            "id_usuario": nuevo.id_usuario,
            "nombre_usuario": nuevo.nombre_usuario,
            "correo_electronico": nuevo.correo_electronico,
            "rol": nuevo.rol
        }
    }