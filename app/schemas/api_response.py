from typing import Generic, TypeVar, Optional
from pydantic import BaseModel
from app.core.responses import ResponseCode

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    success: bool   # True si todo salió bien, False si hubo error
    message: str    # mensaje de estado
    code: int       # 0 = OK, >0 diferentes tipos de error
    detail: str     # Mensaje detallado del error
    data: Optional[T] = None  # datos opcionales

    @classmethod
    def from_enum(cls, response_code: ResponseCode, data: Optional[T] = None, detail: Optional[str] = None):
        return cls(
            success=response_code == ResponseCode.SUCCESS,
            code=response_code.code,
            message=response_code.message,
            detail=detail,
            data=data
        )