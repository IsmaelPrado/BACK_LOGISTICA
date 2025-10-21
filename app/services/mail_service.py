# app/services/mail_service.py
from datetime import datetime
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from app.core.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    TEMPLATE_FOLDER='./app/templates'
)

fm = FastMail(conf)

class MailService:
    async def send_otp_email(self, email: EmailStr, otp: str, nombre_usuario: str):
        message = MessageSchema(
            subject="Tu código de verificación",
            recipients=[email],
            template_body={"nombre_usuario": nombre_usuario, "otp": otp},
            subtype=MessageType.html
        )
        await fm.send_message(message, template_name="otp_email.html")

    async def send_username_recovery_email(self, email: EmailStr, username: str):
        message = MessageSchema(
            subject="Recuperación de nombre de usuario",
            recipients=[email],
            template_body={"nombre_usuario": username},
            subtype=MessageType.html
        )
        await fm.send_message(message, template_name="username_recovery_email.html")

    async def send_password_reset_email(self, email: EmailStr, reset_link: str):
        message = MessageSchema(
            subject="Restablecimiento de contraseña",
            recipients=[email],
            template_body={"reset_link": reset_link},
            subtype=MessageType.html
        )
        await fm.send_message(message, template_name="password_reset_email.html")

    async def send_stock_alert_email(self, email: EmailStr, productos: list):
        """
        Envía un correo de alerta de stock bajo con la lista de productos.
        
        Args:
            email (EmailStr): Correo del destinatario.
            productos (list): Lista de productos, cada uno con:
                - name
                - code
                - barcode
                - sale_price
                - inventory
                - min_inventory
                - category
        """
        now = datetime.utcnow().strftime("%d/%m/%Y %H:%M")
        message = MessageSchema(
            subject="⚠️ Alerta de Stock Bajo",
            recipients=[email],
            template_body={
                "productos": productos,
                "now": now
            },
            subtype=MessageType.html
        )
        # Envía el mensaje usando tu instancia de FastAPI-Mail
        await fm.send_message(message, template_name="low_stock_alert.html")