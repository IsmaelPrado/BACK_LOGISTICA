import logging
from typing import List
from fastapi import APIRouter, Depends, Security
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.api_response import APIResponse
from app.schemas.user import UsuarioCreateRequest, UsuarioCreateResponse, UsuarioDeleteRequest
from app.services import AdminUserService
from app.core.enums.responses import ResponseCode
from app.dependencies.auth import admin_session_required


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/users", 
    tags=["admin_users"],
    dependencies=[Security(admin_session_required)]
)

# -----------------------------
# Crear usuario (solo admins)
# -----------------------------

@router.post("/", response_model=APIResponse)
async def crear_usuario(
    usuario_request: UsuarioCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    service = AdminUserService(db)
    usuario = await service.crear_usuario(usuario_request)
    permisos_nombres = [perm.nombre for perm in usuario.permisos] if usuario.permisos else []

    usuario_resp = UsuarioCreateResponse(
        id_usuario=usuario.id_usuario,
        nombre_usuario=usuario.nombre_usuario,
        correo_electronico=usuario.correo_electronico,
        rol=usuario.rol,
        secret_2fa=usuario.secret_2fa,
        fecha_creacion=usuario.fecha_creacion,
        permisos=permisos_nombres
    )

    return APIResponse.from_enum(
        ResponseCode.SUCCESS,
        data=usuario_resp,
        detail="Usuario creado exitosamente"
    )

# -----------------------------
# Eliminar usuario (solo admins)
# -----------------------------

@router.delete("/", response_model=APIResponse)
async def eliminar_usuario(
    delete_request: UsuarioDeleteRequest,
    db: AsyncSession = Depends(get_db)
):
    service = AdminUserService(db)
    await service.eliminar_usuario_por_nombre(delete_request.nombre_usuario)
    return APIResponse.from_enum(
        ResponseCode.SUCCESS,
        detail="Usuario eliminado exitosamente"
    )
