from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.user_service import authenticate_user
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
