# services/ticket_config_service.py
import json
import base64
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.ticket_configuration import TicketConfiguration


class TicketConfigService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user(self, user_id: int) -> Optional[TicketConfiguration]:
        q = select(TicketConfiguration).filter(TicketConfiguration.user_id == user_id)
        result = await self.db.execute(q)
        return result.scalars().first()
    
    async def get_or_create_default(self, user_id: int) -> TicketConfiguration:
        """Si no existe config, crea una nueva por defecto y la retorna."""
        existing = await self.get_by_user(user_id)

        if existing:
            return existing

        # Crear default config
        default_cfg = self.generate_default_config()
        config_json = json.dumps(default_cfg, ensure_ascii=False)

        new = TicketConfiguration(
            user_id=user_id,
            name="Default",
            config_json=config_json,
            logo=None
        )

        self.db.add(new)
        await self.db.commit()
        await self.db.refresh(new)

        return new


    async def create_or_update(self, user_id: int, name: Optional[str], config_dict: dict, logo_base64: Optional[str] = None) -> TicketConfiguration:
        """
        Crea o actualiza la configuración de ticket para el usuario.
        - config_dict: diccionario con la configuración serializable a JSON.
        - logo_base64: si viene, decodificar y guardar los bytes (puede ser None).
        """
        # Serializamos JSON con indent minimal
        config_json = json.dumps(config_dict, ensure_ascii=False)

        existing = await self.get_by_user(user_id)
        logo_bytes = None
        if logo_base64:
            try:
                # logo_base64 puede venir con header: "data:image/png;base64,...."
                if "," in logo_base64:
                    logo_base64 = logo_base64.split(",", 1)[1]
                logo_bytes = base64.b64decode(logo_base64)
            except Exception:
                logo_bytes = None

        if existing:
            existing.config_json = config_json
            existing.name = name
            if logo_bytes is not None:
                existing.logo = logo_bytes
            self.db.add(existing)
            await self.db.commit()
            await self.db.refresh(existing)
            return existing

        # crear nuevo
        new = TicketConfiguration(
            user_id=user_id,
            name=name,
            config_json=config_json,
            logo=logo_bytes
        )
        self.db.add(new)
        await self.db.commit()
        await self.db.refresh(new)
        return new

    async def delete_for_user(self, user_id: int) -> None:
        existing = await self.get_by_user(user_id)
        if existing:
            await self.db.delete(existing)
            await self.db.commit()

    def generate_default_config(self) -> dict:
        """Config básica por defecto al crear un ticket config nuevo."""
        return {
            "ShopName": "PAPELERÍA CENTRAL",
            "show_shop_name": True,
            "address": "",
            "show_address": True,
            "phone": "",
            "show_phone": True,
            "show_attendant": True,
            "attendant_label": "Le ha atendido:",
            "show_datetime": True,
            "datetime_format": "yyyy-MM-dd HH:mm",
            "show_logo": True,
            "logo_max_width": 120,
            "logo_max_height": 60,
            "font_name": "Consolas",
            "font_size": 9,
            "use_monospace_font": True,
            "separator_char": "-",
            "separator_repeat": 32,
            "show_separators": True,
            "col_articulo": 16,
            "col_cantidad": 4,
            "col_precio": 6,
            "col_importe": 6,
            "show_footer_message": True,
            "footer_message": "Muchas gracias por su compra",
            "show_custom_phrase": False,
            "custom_phrase": "",
            "show_currency_symbol": True
        }

