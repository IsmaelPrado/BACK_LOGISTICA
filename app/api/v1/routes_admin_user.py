import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.models.permiso import Permiso
from app.schemas.api_response import APIResponse
from app.schemas.user import UsuarioCreateRequest, UsuarioCreateResponse
from app.services.admin_user_service import AdminUserService
from app.core.responses import ResponseCode
from app.dependencies.auth import admin_session_required


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/users", tags=["admin_users"])

# -----------------------------
# Crear usuario (solo admins)
# -----------------------------

@router.post("/", response_model=APIResponse)
async def crear_usuario(
    usuario_request: UsuarioCreateRequest,
    db: AsyncSession = Depends(get_db),
    usuario_admin = Depends(admin_session_required)
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
