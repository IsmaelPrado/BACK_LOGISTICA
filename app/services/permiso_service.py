from sqlalchemy import select

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permiso import Permiso
from app.schemas.permiso import PermisoResponse

class PermisoService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_permisos(self) -> List[PermisoResponse]:
        query = select(Permiso).order_by(Permiso.id_permiso)
        result = await self.db.execute(query)
        permisos = result.scalars().all()

        return [
            PermisoResponse.model_validate(p)
            for p in permisos
        ]
