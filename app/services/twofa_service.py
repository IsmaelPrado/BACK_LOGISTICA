import pyotp
import qrcode
import io
import base64
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import Usuario 

class TwoFAService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generar_qr_desde_usuario(self, username: str) -> str:
        """
        Busca el usuario por username, obtiene su secret_2fa y genera un QR en base64.
        """
        # Buscar usuario
        result = await self.db.execute(select(Usuario).where(Usuario.nombre_usuario == username))
        user = result.scalars().first()

        if not user:
            raise ValueError("Usuario no encontrado")

        if not user.secret_2fa:
            raise ValueError("Usuario no tiene secret 2FA configurado")

        # Generar URI TOTP y QR
        totp = pyotp.TOTP(user.secret_2fa)
        uri = totp.provisioning_uri(name=user.correo_electronico, issuer_name="MiApp")

        qr = qrcode.make(uri)
        buffer = io.BytesIO()
        qr.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return qr_base64

    async def configurar_2fa_para_usuario(self, username: str) -> str:
        """
        Genera un nuevo secret_2fa para el usuario si no tiene, lo guarda y retorna el QR.
        """
        # Buscar usuario
        result = await self.db.execute(select(Usuario).where(Usuario.nombre_usuario == username))
        user = result.scalars().first()

        if not user:
            raise ValueError("Usuario no encontrado")

        # Generar secret si no tiene
        if not user.secret_2fa:
            secret = pyotp.random_base32()
            user.secret_2fa = secret
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)

        # Generar QR
        totp = pyotp.TOTP(user.secret_2fa)
        uri = totp.provisioning_uri(name=user.correo_electronico, issuer_name="MiApp")

        qr = qrcode.make(uri)
        buffer = io.BytesIO()
        qr.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return qr_base64

    @staticmethod
    def verificar_codigo(secret: str, code: str) -> bool:
        """
        Verifica el código TOTP proporcionado por el usuario.
        """
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)  # ±30s de tolerancia
