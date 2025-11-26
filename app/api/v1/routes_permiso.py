from fastapi import APIRouter, Depends, Security
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.dependencies.auth import permission_required
from app.schemas.api_response import APIResponse
from app.core.enums.responses import ResponseCode
from app.services.permiso_service import PermisoService

router = APIRouter(
    prefix="/permisos", 
    tags=["permisos"],
    )

@router.get("/listar", response_model=APIResponse)
async def listar_permisos(
    db: AsyncSession = Depends(get_db),
    usuario=Depends(permission_required("ver_permisos"))
):
    service = PermisoService(db)
    try:
        permisos = await service.get_all_permisos()

        return APIResponse.from_enum(
            ResponseCode.SUCCESS,
            data=permisos,
            detail="Lista de permisos obtenida correctamente"
        )

    except Exception as e:
        return APIResponse.from_enum(
            ResponseCode.SERVER_ERROR,
            detail=f"Ocurrió un error inesperado: {str(e)}"
        )
