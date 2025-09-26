from fastapi import APIRouter, Depends, HTTPException, Response, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.api_response import APIResponse
from app.schemas.auth import GoogleAuthResponse, GoogleUser, LoginRequest, DefaultResponse, LoginResponse, OTPRequest, PasswordRecoveryRequest, PasswordResetRequest, SessionResponse, TokenData, UsuarioRequest, UsuarioResponse, UsernameRecoveryRequest
from app.services.geo_service import GeoService
from app.services.google_oauth import GoogleOAuthService
from app.services.mail_service import MailService
from app.services.session_service import SessionService
from app.services.twofa_service import TwoFAService
from app.services.user_service import UserService
from app.core.security import create_access_token, generate_state, get_client_ip
from app.models.user import Usuario
import logging
from app.core.limiter import limiter
from app.services.otp_service import OTPService
from app.core.responses import ResponseCode
from app.core.dependencies import get_current_user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# Servicios
mail_service = MailService()
google_oauth_service = GoogleOAuthService()


# @router.get("/me", response_model=APIResponse)
# async def me(current_user = Depends(get_current_user)):
#     return APIResponse.from_enum(ResponseCode.SUCCESS, data={"username": current_user.nombre_usuario, "email": current_user.correo_electronico})

@router.post(
        "/login", 
        response_model=APIResponse[LoginResponse], 
        status_code=status.HTTP_200_OK
        )
@limiter.limit("5/minute")
async def login_step1(
    request: Request,
    login_request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        
        user_service = UserService(db)
        user: Usuario = await user_service.authenticate_user(login_request.username, login_request.password)
        twofa_service = TwoFAService(db)
        qr_base64 = await twofa_service.configurar_2fa_para_usuario(login_request.username)
    except ValueError as e:
        logger.warning(f"Error de autenticación para usuario {login_request.username}: {e}")
        return APIResponse.from_enum(
            ResponseCode.AUTHENTICATION_FAILED,
            detail=str(e)
        )
        
    if login_request.login_type == "email":
           # Generar OTP
        otp_service = OTPService(db)
        otp = await otp_service.generate_otp(user.id_usuario)

        # Enviar OTP por correo usando el service
        await mail_service.send_otp_email(user.correo_electronico, otp, user.nombre_usuario)
        return APIResponse.from_enum(
            ResponseCode.SUCCESS,
            detail="OTP enviado al correo. Por favor verifica para continuar"
        )
    
    elif login_request.login_type == "totp":
        if not user.secret_2fa:
            return APIResponse.from_enum(
                ResponseCode.BAD_REQUEST,
                detail="El usuario no tiene configurado 2FA con Google Authenticator"
            )

        return APIResponse.from_enum(
            ResponseCode.SUCCESS,
            detail="Usuario autenticado. Ingresa tu código de Google Authenticator.",
            data=LoginResponse(
                qr_base64=qr_base64
            )
        )
    else :
        return APIResponse.from_enum(
                ResponseCode.BAD_REQUEST, 
                detail="Tipo de login inválido"
            )



@router.post(
    "/login-step2-email",
    response_model=APIResponse[SessionResponse],
    status_code=status.HTTP_200_OK
)
@limiter.limit("5/minute")
async def login_step2(
    request: Request,
    otp_request: OTPRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Usuario).where(Usuario.nombre_usuario == otp_request.username))
    user = result.scalars().first()
    if not user:
        return APIResponse.from_enum(ResponseCode.NOT_FOUND, detail="Usuario no encontrado")

    otp_service = OTPService(db)
    is_valid = await otp_service.verify_otp(user.id_usuario, otp_request.otp)
    if not is_valid:
        return APIResponse.from_enum(ResponseCode.AUTHENTICATION_FAILED, detail="OTP inválido o expirado")

    session_service = SessionService(db)
    client_ip = request.client.host
    lat, lon = await GeoService.get_geolocation_from_ip(client_ip)
    sesion, nueva, tiempo_restante = await session_service.crear_o_actualizar_sesion(
        id_usuario=user.id_usuario,
        latitud=lat,
        longitud=lon
    )

    if not nueva:
        return APIResponse.from_enum(
            ResponseCode.SUCCESS,
            detail="El usuario ya tiene una sesión activa.",
            data=SessionResponse(
                session_id=sesion.id,
                fecha_inicio=sesion.fecha_inicio,
                estado=sesion.estado,
                latitud=sesion.latitud,
                longitud=sesion.longitud,
                tiempo_restante=tiempo_restante
            )
        )

    return APIResponse.from_enum(
        ResponseCode.SUCCESS,
        detail="Usuario autenticado. Sesión creada correctamente.",
        data=SessionResponse(
            session_id=sesion.id,
            fecha_inicio=sesion.fecha_inicio,
            estado=sesion.estado,
            latitud=sesion.latitud,
            longitud=sesion.longitud,
            tiempo_restante=None
        )
    )


@router.post(
    "/login-step2-totp",
    response_model=APIResponse[SessionResponse],
    status_code=status.HTTP_200_OK
)
@limiter.limit("5/minute")
async def login_step2_totp(
    request: Request,
    otp_request: OTPRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Usuario).where(Usuario.nombre_usuario == otp_request.username))
    user = result.scalars().first()
    if not user:
        return APIResponse.from_enum(ResponseCode.NOT_FOUND, detail="Usuario no encontrado")

    if not user.secret_2fa:
        return APIResponse.from_enum(ResponseCode.BAD_REQUEST, detail="Usuario no tiene 2FA configurado")

    if not TwoFAService.verificar_codigo(user.secret_2fa, otp_request.otp):
        return APIResponse.from_enum(ResponseCode.AUTHENTICATION_FAILED, detail="Código inválido o expirado")

    session_service = SessionService(db)
    client_ip = request.client.host
    lat, lon = await GeoService.get_geolocation_from_ip(client_ip)
    sesion, nueva, tiempo_restante = await session_service.crear_o_actualizar_sesion(
        id_usuario=user.id_usuario,
        latitud=lat,
        longitud=lon
    )

    if not nueva:
        return APIResponse.from_enum(
            ResponseCode.SUCCESS,
            detail="El usuario ya tiene una sesión activa.",
            data=SessionResponse(
                session_id=sesion.id,
                fecha_inicio=sesion.fecha_inicio,
                estado=sesion.estado,
                latitud=sesion.latitud,
                longitud=sesion.longitud,
                tiempo_restante=tiempo_restante
            )
        )

    return APIResponse.from_enum(
        ResponseCode.SUCCESS,
        detail="Usuario autenticado. Sesión creada correctamente.",
        data=SessionResponse(
            session_id=sesion.id,
            fecha_inicio=sesion.fecha_inicio,
            estado=sesion.estado,
            latitud=sesion.latitud,
            longitud=sesion.longitud,
            tiempo_restante=tiempo_restante
        )
    )


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

@router.get(
    "/google/callback",
    response_model=APIResponse[SessionResponse],
    status_code=status.HTTP_200_OK
)
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
        return APIResponse.from_enum(ResponseCode.BAD_REQUEST, detail="State inválido o sospechoso")

    if error:
        return APIResponse.from_enum(ResponseCode.BAD_REQUEST, detail=f"Error en login con Google: {error}")
    if not code:
        return APIResponse.from_enum(ResponseCode.BAD_REQUEST, detail="No se recibió código de autorización")

    # 1. Intercambiamos code por access_token
    token_data = await google_oauth_service.exchange_code_for_token(code)
    access_token = token_data.get("access_token")
    if not access_token:
        return APIResponse.from_enum(ResponseCode.AUTHENTICATION_FAILED, detail="No se pudo obtener access_token de Google")

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
            rol="usuario",  # contraseña vacía porque login es externo
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        user = new_user

    # 4. Crear Sesión
    session_service = SessionService(db)
    client_ip = request.client.host
    lat, lon = await GeoService.get_geolocation_from_ip(client_ip)
    nueva_sesion = await session_service.crear_sesion(
        id_usuario=user.id_usuario,
        latitud=lat,
        longitud=lon
    )

    return APIResponse.from_enum(
        ResponseCode.SUCCESS,
        detail="Usuario autenticado con Google. Sesión creada correctamente.",
        data=SessionResponse(
            session_id=nueva_sesion.id,
            fecha_inicio=nueva_sesion.fecha_inicio,
            estado=nueva_sesion.estado,
            latitud=nueva_sesion.latitud,
            longitud=nueva_sesion.longitud
        )
    )



@router.post("/register", response_model=APIResponse[UsuarioResponse], status_code=status.HTTP_201_CREATED)
async def register_user(user: UsuarioRequest, db: AsyncSession = Depends(get_db)):
    try:
        user_service = UserService(db)
        nuevo = await user_service.create_user(user)
    except ValueError as e:
        logger.warning(f"Error al registrar usuario {user.nombre_usuario}: {e}")
        return APIResponse.from_enum(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return APIResponse(
        detail="Usuario registrado correctamente",
        result=UsuarioResponse(
            id_usuario=nuevo.id_usuario,
            nombre_usuario=nuevo.nombre_usuario,
            correo_electronico=nuevo.correo_electronico,
            rol=nuevo.rol
        )
    )


@router.post("/recover-user", response_model=APIResponse, status_code=status.HTTP_200_OK)
@limiter.limit("3/minute")
async def recover_user(
    request: Request,
    username_recovery_request: UsernameRecoveryRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        user_service = UserService(db)
        user: Usuario | None = await user_service.get_user_by_email(username_recovery_request.email)
        if not user:
            return APIResponse.from_enum(
                ResponseCode.NOT_FOUND, 
                detail="Usuario no encontrado"
            )

        await mail_service.send_username_recovery_email(user.correo_electronico, user.nombre_usuario)

        return APIResponse.from_enum(
            ResponseCode.SUCCESS,
            detail="Correo de recuperación enviado."
        )

    except Exception as e:
        logger.error(f"Error en recover_user: {e}")
        return APIResponse.from_enum(
            ResponseCode.SERVER_ERROR,
            detail=str(e)
        )



@router.post("/recover-password", response_model=APIResponse, status_code=status.HTTP_200_OK)
@limiter.limit("3/minute")
async def recover_password(
    request: Request,
    password_request: PasswordRecoveryRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        user_service = UserService(db)
        user: Usuario | None = await user_service.get_user_by_username(password_request.username)
        if not user:
            return APIResponse.from_enum(
                ResponseCode.NOT_FOUND, 
                detail="Usuario no encontrado"
            )

        reset = await user_service.create_password_reset(user)

        # Enviar correo
        reset_link = f"https://cips.com/reset-password?token={reset.reset_token}"
        await mail_service.send_password_reset_email(user.correo_electronico, reset_link)

        return APIResponse.from_enum(
            ResponseCode.SUCCESS,
            detail="Correo de recuperación enviado."
        )

    except Exception as e:
        logger.error(f"Error en recover_password: {e}")
        return APIResponse.from_enum(
            ResponseCode.SERVER_ERROR,
            detail=str(e)
        )


@router.post("/reset-password", response_model=APIResponse, status_code=status.HTTP_200_OK)
async def reset_password(
    request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        user_service = UserService(db)
        
        reset = await user_service.verify_password_reset(request.token)  
        if not reset:
            return APIResponse.from_enum(
                ResponseCode.NOT_FOUND,
                detail="Token inválido o expirado"
            )

        if request.new_password != request.confirm_new_password:
            return APIResponse.from_enum(
                ResponseCode.VALIDATION_ERROR,
                detail="Las contraseñas no coinciden"
            )

        user = await user_service.get_user_by_id(reset.user_id)
        await user_service.update_password(user, request.new_password)

        # Borrar el token una vez usado
        await db.delete(reset)
        await db.commit()

        return APIResponse.from_enum(
            ResponseCode.SUCCESS,
            detail="Contraseña restablecida correctamente"
        )

    except Exception as e:
        logger.error(f"Error en reset_password: {e}")
        return APIResponse.from_enum(
            ResponseCode.SERVER_ERROR,
            detail=str(e)
        )
