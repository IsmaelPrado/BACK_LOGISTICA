# schemas/ticket_config.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TicketConfigBase(BaseModel):
    # Encabezado
    shop_name: Optional[str] = Field("PAPELERÍA CENTRAL", alias="ShopName")
    show_shop_name: Optional[bool] = True

    address: Optional[str] = ""
    show_address: Optional[bool] = True

    phone: Optional[str] = ""
    show_phone: Optional[bool] = True

    show_attendant: Optional[bool] = True
    attendant_label: Optional[str] = "Le ha atendido:"

    show_datetime: Optional[bool] = True
    datetime_format: Optional[str] = "yyyy-MM-dd HH:mm"

    # Logo
    show_logo: Optional[bool] = True
    logo_base64: Optional[str] = None  # Base64 string opcional en request/response
    logo_max_width: Optional[int] = 120
    logo_max_height: Optional[int] = 60

    # Tipografía
    font_name: Optional[str] = "Consolas"
    font_size: Optional[float] = 9.0
    use_monospace_font: Optional[bool] = True

    # Separadores
    separator_char: Optional[str] = "-"
    separator_repeat: Optional[int] = 32
    show_separators: Optional[bool] = True

    # Column widths
    col_articulo: Optional[int] = 16
    col_cantidad: Optional[int] = 4
    col_precio: Optional[int] = 6
    col_importe: Optional[int] = 6

    # Footer
    show_footer_message: Optional[bool] = True
    footer_message: Optional[str] = "Muchas gracias por su compra"
    show_custom_phrase: Optional[bool] = False
    custom_phrase: Optional[str] = ""

    # Otras opciones
    show_currency_symbol: Optional[bool] = True

    class Config:
        allow_population_by_field_name = True
        orm_mode = True


class TicketConfigCreateUpdate(TicketConfigBase):
    name: Optional[str] = "Default"


class TicketConfigResponse(TicketConfigBase):
    id: int
    user_id: int
    name: Optional[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
