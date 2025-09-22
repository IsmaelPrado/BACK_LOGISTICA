from fastapi import APIRouter, Depends, HTTPException, Response, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.auth import GoogleAuthResponse, GoogleUser, LoginRequest, DefaultResponse, LoginResponse, OTPRequest, OTPResponse, PasswordRecoveryRequest, PasswordResetRequest, UsuarioRequest, UsuarioResponse, UsernameRecoveryRequest
from app.services.google_oauth import GoogleOAuthService
from app.services.mail_service import MailService
from app.services.twofa_service import TwoFAService
from app.services.user_service import UserService
from app.core.security import create_access_token, generate_state
from app.models.user import Usuario
import logging
from app.core.limiter import limiter
from app.services.otp_service import OTPService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# Servicios
mail_service = MailService()
google_oauth_service = GoogleOAuthService()


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
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
    if login_request.login_type == "email":
           # Generar OTP
        otp_service = OTPService(db)
        otp = await otp_service.generate_otp(user.id_usuario)

        # Enviar OTP por correo usando el service
        await mail_service.send_otp_email(user.correo_electronico, otp, user.nombre_usuario)


        return LoginResponse(detail="OTP enviado al correo. Por favor verifica para continuar.")
    elif login_request.login_type == "totp":
        twofa_service = TwoFAService(db)
        if not user.secret_2fa:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El usuario no tiene configurado 2FA con Google Authenticator"
            )
        qr_base64 = await twofa_service.configurar_2fa_para_usuario(login_request.username)
        return LoginResponse(
            detail="Usuario autenticado. Ingresa tu código de Google Authenticator.",
            qr_base64=qr_base64
            )
    else :
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tipo de login inválido")

 


@router.post("/login-step2-email", response_model=OTPResponse, status_code=status.HTTP_200_OK)
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


@router.post("/login-step2-totp", response_model=OTPResponse, status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def login_step2_totp(
    request: Request,
    otp_request: OTPRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Usuario).where(Usuario.nombre_usuario == otp_request.username))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    if not user.secret_2fa:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario no tiene 2FA configurado")

    # Verificar OTP TOTP
    if not TwoFAService.verificar_codigo(user.secret_2fa, otp_request.otp):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Código inválido o expirado")

    # Generar JWT
    access_token = create_access_token(data={"sub": user.nombre_usuario, "rol": user.rol})
    return OTPResponse(access_token=access_token)


# Login con Google OAuth
@router.get("/login/google")
async def google_login():
    state = generate_state()
    login_url = google_oauth_service.get_google_login_url(state=state)

    response = RedirectResponse(url=login_url)
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        samesite="lax",  
        secure=False      
    )
    return response

@router.get("/google/callback", response_model=GoogleAuthResponse, status_code=status.HTTP_200_OK)
async def google_callback(
    request: Request,
    code: str | None = None, 
    state: str | None = None, 
    error: str | None = None, 
    db: AsyncSession = Depends(get_db)
    ):
    """Google redirige aquí después de login"""
    state_cookie = request.cookies.get("oauth_state")
    if state != state_cookie:
        raise HTTPException(status_code=400, detail="State inválido o sospechoso")

    if error:
        raise HTTPException(status_code=400, detail=f"Error en login con Google: {error}")
    if not code:
        raise HTTPException(status_code=400, detail="No se recibió código de autorización")

    # 1. Intercambiamos code por access_token
    token_data = await google_oauth_service.exchange_code_for_token(code)
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No se pudo obtener access_token de Google")

    # 2. Obtenemos info del usuario
    user_info = await google_oauth_service.get_user_info(access_token)
    google_user = GoogleUser(**user_info)

    # 3. Buscar o crear usuario en tu BD
    result = await db.execute(
        Usuario.__table__.select().where(Usuario.correo_electronico == google_user.email)
    )
    user = result.fetchone()

    if not user:
        new_user = Usuario(
            nombre_usuario=google_user.email,
            correo_electronico=google_user.email,
            contrasena="",
            rol="usuario",
            # contraseña podría ser None porque login es externo
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        user = new_user

    # 4. Crear JWT propio de tu sistema
    jwt_token = create_access_token({"sub": str(user.id_usuario), "rol": user.rol})

    return GoogleAuthResponse(
        access_token=jwt_token,
        user=google_user
    )


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
    user: Usuario | None = await user_service.get_user_by_email(username_recovery_request.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    await mail_service.send_username_recovery_email(user.correo_electronico, user.nombre_usuario)

    return DefaultResponse(detail="Correo de recuperación enviado.")

@router.post("/recover-password", response_model=DefaultResponse)
@limiter.limit("3/minute")
async def recover_password(request: Request, password_request: PasswordRecoveryRequest, db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    user: Usuario | None = await user_service.get_user_by_username(password_request.username)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    reset = await user_service.create_password_reset(user)

    # Enviar correo
    reset_link = f"https://cips.com/reset-password?token={reset.reset_token}"
    await mail_service.send_password_reset_email(user.correo_electronico, reset_link)

    return DefaultResponse(detail="Correo de recuperación enviado.")

@router.post("/reset-password", response_model=DefaultResponse)
async def reset_password(request: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    
    reset = await user_service.verify_password_reset(request.token)  
    if not reset:
        raise HTTPException(status_code=400, detail="Token inválido o expirado")

    if request.new_password != request.confirm_new_password:
        raise HTTPException(status_code=400, detail="Las contraseñas no coinciden")

    try:
        user = await user_service.get_user_by_id(reset.user_id)
        await user_service.update_password(user, request.new_password)
    except ValueError as e:
        logger.warning(f"Error al restablecer la contraseña para usuario {user.nombre_usuario}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Borrar el token una vez usado
    await db.delete(reset)
    await db.commit()

    return DefaultResponse(detail="Contraseña restablecida correctamente")
