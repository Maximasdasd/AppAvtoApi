from pydantic import BaseModel, Field, field_validator, field_serializer
from models.model import UserRole
from typing import Optional
from datetime import datetime

class StaffBase(BaseModel):
    username: str
    full_name: str
    email: str
    phone: str
    position: UserRole



class StaffCreate(StaffBase):
    password: str


class StaffResponsePublic(StaffBase):
    staff_id: int

class GetToken(BaseModel):
    refresh_token: str
    access_token: str
    token_type: str