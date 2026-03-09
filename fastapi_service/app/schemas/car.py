from pydantic import BaseModel
from models.model import CarCategory, CarStatus
class CarBase(BaseModel):
    number_car: str
    brand: str
    color: str
    year: int
    category: CarCategory
    daily_price: float

class CreateCar(CarBase):
    pass

class CarResponse(CarBase):
    car_id: int
    is_available: CarStatus

