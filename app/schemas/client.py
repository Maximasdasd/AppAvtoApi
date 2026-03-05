from pydantic import BaseModel, Field, field_validator, field_serializer
from typing import Optional
from datetime import datetime

class ClientBase(BaseModel):
    full_name: str
    driver_license: str = Field(max_length=9, min_length=9)
    passport: str
    address: Optional[str]
    # @field_validator("driver_license")
    # @classmethod
    # def validate_driver_license(cls, value):
    #     if value is None:
    #         return value
    #     if len(value) != 9:
    #         # print(f"Warning: Driver license '{value}' has length {len(value)}")
    #         raise ValueError('должно быть 9 символов')
    #     return value


class ClientCreate(ClientBase):
    pass


class ClientResponse(ClientBase):
    client_id: int
    created_at: datetime
    is_active: bool
    @field_serializer('created_at')
    def serialize_created_at(self, value: datetime) -> str:
        return value.strftime('%Y-%m-%d %H:%M')
