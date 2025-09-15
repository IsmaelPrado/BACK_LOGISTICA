from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.auth import LoginRequest, DefaultResponse, OTPRequest, OTPResponse, UsuarioRequest, UsuarioResponse, UsernameRecoveryRequest
from app.services.mail_service import MailService
from app.services.user_service import UserService
from app.core.security import create_access_token
from app.models.user import Usuario
import logging
from app.core.limiter import limiter
from app.services.otp_service import OTPService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def login_step1(
    request: Request,
    login_request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        user_service = UserService(db)
        user: Usuario = await user_service.authenticate_user(login_request.username, login_request.password)
    except ValueError as e:
        logger.warning(f"Error de autenticación para usuario {login_request.username}: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    # Generar OTP
    otp_service = OTPService(db)
    otp = await otp_service.generate_otp(user.id_usuario)

    # Enviar OTP por correo usando el service
    mail_service = MailService()
    await mail_service.send_otp_email(user.correo_electronico, otp, user.nombre_usuario)


    return DefaultResponse(detail="OTP enviado al correo. Por favor verifica para continuar.")


@router.post("/login/verify", response_model=OTPResponse, status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def login_step2(
    request: Request,
    otp_request: OTPRequest,
    db: AsyncSession = Depends(get_db)
):
    # Obtener usuario por username
    result = await db.execute(select(Usuario).where(Usuario.nombre_usuario == otp_request.username))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    # Verificar OTP
    otp_service = OTPService(db)
    is_valid = await otp_service.verify_otp(user.id_usuario, otp_request.otp)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="OTP inválido o expirado")

    # Generar token
    access_token = create_access_token(data={"sub": user.nombre_usuario, "rol": user.rol})

    return OTPResponse(access_token=access_token)


@router.post("/register", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: UsuarioRequest, db: AsyncSession = Depends(get_db)):
    try:
        user_service = UserService(db)
        nuevo = await user_service.create_user(user)
    except ValueError as e:
        logger.warning(f"Error al registrar usuario {user.nombre_usuario}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)  
        )

    return UsuarioResponse(
        id_usuario=nuevo.id_usuario,
        nombre_usuario=nuevo.nombre_usuario,
        correo_electronico=nuevo.correo_electronico,
        rol=nuevo.rol
    )

@router.post("/recover-user", response_model=DefaultResponse, status_code=status.HTTP_200_OK)
@limiter.limit("3/minute")
async def recover_user(request: Request, username_recovery_request: UsernameRecoveryRequest, db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    user = await user_service.get_user_by_email(username_recovery_request.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    mail_service = MailService()
    await mail_service.send_username_recovery_email(user.correo_electronico, user.nombre_usuario)

    return DefaultResponse(detail="Correo de recuperación enviado.")