from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.api_response import APIResponse, ResponseCode
from app.schemas.user import UserPerfilResponse
from app.services.user_service import UserService
from app.dependencies.auth import permission_required

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/perfil", response_model=APIResponse[UserPerfilResponse])
async def obtener_perfil_usuario(
    request: Request,
    db: AsyncSession = Depends(get_db),
    usuario=Depends(permission_required("ver_perfil"))
):
    """
    👤 Obtiene la información del perfil del usuario autenticado mediante el token de sesión.
    """
    try:
        # Extraer el token directamente del header Authorization
        token = request.headers.get("Authorization")
        if not token:
            return APIResponse.from_enum(
                ResponseCode.AUTHORIZATION_DENIED,
                detail="Token de sesión no proporcionado."
            )

        # Instanciar servicio y obtener perfil
        service = UserService(db)
        user = await service.obtener_perfil_usuario(token)

        return APIResponse.from_enum(
            ResponseCode.SUCCESS,
            data=user,
            detail=f"Perfil del usuario '{user.nombre_usuario}' obtenido exitosamente."
        )

    except ValueError as e:
        return APIResponse.from_enum(
            ResponseCode.VALIDATION_ERROR,
            detail=str(e)
        )
    except Exception as e:
        return APIResponse.from_enum(
            ResponseCode.SERVER_ERROR,
            detail=f"Ocurrió un error inesperado: {str(e)}"
        )
