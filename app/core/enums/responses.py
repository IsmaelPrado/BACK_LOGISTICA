from typing import Generic, TypeVar, Optional
from pydantic import BaseModel
from enum import Enum

T = TypeVar("T")

class ResponseCode(Enum):
    SUCCESS = (0, "Success")
    VALIDATION_ERROR = (1, "Validation error")
    AUTHENTICATION_FAILED = (2, "Authentication failed")
    AUTHORIZATION_DENIED = (3, "Authorization denied")
    NOT_FOUND = (4, "Resource not found")
    SERVER_ERROR = (5, "Internal server error")
    TIMEOUT = (6, "Request timeout")
    CONFLICT = (7, "Conflict detected")
    BAD_REQUEST = (8, "Bad request")
    FORBIDDEN = (9, "Forbidden access")
    DUPLICATE_ENTRY = (10, "Duplicate entry")
    INVALID_TOKEN = (11, "Invalid token")
    TOKEN_EXPIRED = (12, "Token expired")
    UNSUPPORTED_OPERATION = (13, "Unsupported operation")
    RATE_LIMIT_EXCEEDED = (14, "Rate limit exceeded")
    DATABASE_ERROR = (15, "Database error")
    UNKNOWN_ERROR = (999, "Unknown error")

    def __init__(self, code: int, message: str):
        self._code = code
        self._message = message

    @property
    def code(self) -> int:
        return self._code

    @property
    def message(self) -> str:
        return self._message