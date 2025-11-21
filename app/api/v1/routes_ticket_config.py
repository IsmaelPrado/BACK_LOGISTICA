from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.ticket_config_service import TicketConfigService
from app.schemas.ticket_config import TicketConfigCreateUpdate, TicketConfigResponse
from app.core.dependencies import get_db
from app.dependencies.auth import permission_required
from app.schemas.api_response import APIResponse
import json
import base64

from app.core.enums.responses import ResponseCode

router = APIRouter(prefix="/me/ticket-config", tags=["TicketConfig"])


# ============================================================
#                        GET CONFIG
# ============================================================
@router.get("/", status_code=status.HTTP_200_OK)
async def get_my_ticket_config(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(permission_required("config_ticket"))
):
    service = TicketConfigService(db)

    try:
        cfg = await service.get_or_create_default(current_user.id_usuario)

        # Parse JSON guardado
        cfg_dict = json.loads(cfg.config_json)

        # Logo opcional en base64
        logo_b64 = None
        if cfg.logo:
            logo_b64 = "data:image/png;base64," + base64.b64encode(cfg.logo).decode()

        response = TicketConfigResponse(
            id=cfg.id,
            user_id=cfg.user_id,
            name=cfg.name,
            created_at=cfg.created_at,
            updated_at=cfg.updated_at,
            **cfg_dict,
            logo_base64=logo_b64
        )

        return APIResponse.from_enum(
            ResponseCode.SUCCESS,
            data=response,
            detail="Configuración de ticket obtenida correctamente."
        )

    except Exception as e:
        return APIResponse.from_enum(
            ResponseCode.SERVER_ERROR,
            detail=f"Error al obtener configuración: {str(e)}"
        )



# ============================================================
#                  CREATE / UPDATE CONFIG
# ============================================================
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_or_update_my_ticket_config(
    payload: TicketConfigCreateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(permission_required("config_ticket"))
):
    service = TicketConfigService(db)

    try:
        # Config JSON (excluyendo logo_base64)
        config_dict = payload.dict(exclude={"logo_base64", "name"}, by_alias=True)
        logo_b64 = payload.logo_base64

        # Crear o actualizar en DB
        cfg = await service.create_or_update(
            user_id=current_user.id_usuario,
            name=payload.name,
            config_dict=config_dict,
            logo_base64=logo_b64
        )

        # Reconstruir para respuesta
        cfg_dict = json.loads(cfg.config_json)

        logo_b64_resp = None
        if cfg.logo:
            logo_b64_resp = "data:image/png;base64," + base64.b64encode(cfg.logo).decode()

        response = TicketConfigResponse(
            id=cfg.id,
            user_id=cfg.user_id,
            name=cfg.name,
            created_at=cfg.created_at,
            updated_at=cfg.updated_at,
            **cfg_dict,
            logo_base64=logo_b64_resp
        )

        return APIResponse.from_enum(
            ResponseCode.SUCCESS,
            data=response,
            detail="Configuración de ticket guardada exitosamente."
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
