from pydantic import BaseModel, Field, field_validator, field_serializer
from models.model import CarStatus, RentalStatus
from typing import Optional
from datetime import datetime

class RentalBase(BaseModel):
    client_id: int
    car_id: int
    end_time: datetime
    start_time: datetime


# client_id=check_client_id,
# car_id=check_car_id,
# staff_id=staff_id,
# status_rent=RentalStatus.ACTIVE,
# start_time=start_time,
# end_time=rent_data.end_time,
# total_hours=total_minutes,
# total_price=total_price

class RentCreate(RentalBase):
    pass

class RentalResponse(RentalBase):
    rental_id: int
    start_time: datetime
    status_rent: RentalStatus
    total_hours: int
    total_price: float
    staff_id: int