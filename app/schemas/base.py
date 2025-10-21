# models/base.py
from pydantic import BaseModel, root_validator
from app.validators.common_validators import validate_strings_recursively

class BaseValidatedModel(BaseModel):
    @root_validator(pre=True)
    def check_invalid_strings(cls, values):
        validate_strings_recursively(values)
        return values
