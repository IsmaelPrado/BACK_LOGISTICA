import secrets
import string
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
from app.models.user_otp import UserOTP
from app.core.config import settings

class OTPService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_otp(self, user_id: int, length: int = settings.OTP_LENGTH, expire_minutes: int = settings.OTP_EXPIRE_MINUTES) -> str:
        """
        Genera un OTP, lo guarda en la DB y devuelve el código.
        """

        await self.db.execute(
            delete(UserOTP).where(UserOTP.user_id == user_id)
        )
        await self.db.commit()

        otp = ''.join(secrets.choice(string.digits) for _ in range(length))
        expire_time = datetime.utcnow() + timedelta(minutes=expire_minutes)

        new_otp = UserOTP(
            user_id=user_id,
            otp=otp,
            expires_at=expire_time
        )
        self.db.add(new_otp)
        await self.db.commit()
        await self.db.refresh(new_otp)

        return otp

    async def verify_otp(self, user_id: int, otp: str) -> bool:
        """
        Verifica si el OTP es válido y no expiró. Si es válido, lo elimina.
        """
        result = await self.db.execute(
            select(UserOTP)
            .where(UserOTP.user_id == user_id)
            .where(UserOTP.otp == otp)
        )
        otp_record = result.scalars().first()

        if not otp_record:
            return False

        if datetime.utcnow() > otp_record.expires_at:
            await self.db.delete(otp_record)
            await self.db.commit()
            return False

        # OTP válido, eliminarlo para que no se pueda reutilizar
        await self.db.delete(otp_record)
        await self.db.commit()
        return True
