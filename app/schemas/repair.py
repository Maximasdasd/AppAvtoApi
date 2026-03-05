from pydantic import BaseModel, Field, field_validator, field_serializer
from typing import Optional
from datetime import datetime

class RepairBase(BaseModel):
    pass

class RepairComplete(RepairBase):
    end_rep: datetime

class RepairCreate(RepairBase):
    car_id: int = Field(foreign_key="cars.car_id")
    start_rep: datetime
    price_rep: float

class RepairResponse(RepairBase):
    repair_id: int
    car_id: int = Field(foreign_key="cars.car_id")
    start_rep: datetime
    end_rep: Optional[datetime]
    price_rep: float
    repair_id: int
