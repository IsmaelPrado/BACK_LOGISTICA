# app/services/mail_service.py
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from fastapi import BackgroundTasks
from app.core.config import settings
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os

# Configura la carpeta donde están tus plantillas HTML
templates_env = Environment(
    loader=FileSystemLoader("./app/templates"),
    autoescape=select_autoescape(["html", "xml"])
)

class MailService:
    def __init__(self):
        self.sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        self.from_email = settings.MAIL_FROM

    def _render_template(self, template_name: str, context: dict) -> str:
        """Renderiza el HTML usando Jinja2."""
        template = templates_env.get_template(template_name)
        return template.render(context)

    async def _send_email(self, to_email: str, subject: str, html_content: str):
        """Envía el correo usando SendGrid."""
        message = Mail(
            from_email=self.from_email,
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )

        try:
            response = self.sg.send(message)
            print(f"[SendGrid] Correo enviado a {to_email}. Código: {response.status_code}")
        except Exception as e:
            print(f"[SendGrid] Error al enviar correo: {e}")

    async def send_otp_email(self, email: str, otp: str, nombre_usuario: str):
        html_content = self._render_template("otp_email.html", {
            "nombre_usuario": nombre_usuario,
            "otp": otp
        })
        await self._send_email(email, "Tu código de verificación", html_content)

    async def send_username_recovery_email(self, email: str, username: str):
        html_content = self._render_template("username_recovery_email.html", {
            "nombre_usuario": username
        })
        await self._send_email(email, "Recuperación de nombre de usuario", html_content)

    async def send_password_reset_email(self, email: str, reset_link: str):
        html_content = self._render_template("password_reset_email.html", {
            "reset_link": reset_link
        })
        await self._send_email(email, "Restablecimiento de contraseña", html_content)

    async def send_stock_alert_email(self, email: str, productos: list):
        now = datetime.utcnow().strftime("%d/%m/%Y %H:%M")
        html_content = self._render_template("low_stock_alert.html", {
            "productos": productos,
            "now": now
        })
        await self._send_email(email, "⚠️ Alerta de Stock Bajo", html_content)
