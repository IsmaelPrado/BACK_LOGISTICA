from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    success: bool   # True si todo salió bien, False si hubo error
    message: str    # mensaje de estado
    code: int       # 0 = OK, >0 diferentes tipos de error
    data: Optional[T] = None  # datos opcionales
