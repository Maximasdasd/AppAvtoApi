# models.py
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from enum import Enum

# enums 
class CarCategory(str, Enum):
    ECONOMY = "ECONOMY"
    STANDARD = "STANDARD"
    PREMIUM = "PREMIUM"
    LUX = "LUX"

class CarStatus(str, Enum):
    AVAILABLE = "available"
    RENTED = "rented"
    UNDER_REPAIR = "under_repair"

class RentalStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class UserRole(str, Enum):
    MANAGER = "manager"
    ADMIN = "admin"
    DIRECTOR = "director"


class Client(SQLModel, table=True):
  client_id: int = Field(primary_key=True)
  full_name: str
  driver_license: str = Field(unique=True) # уникальный номер водительского удостоверения
  passport: str = Field(unique=True)
  address: str
  created_at: datetime = Field(default_factory=datetime.now)
  is_active: bool = Field(default=True)

  eventlog: List["EventLog"] = Relationship(back_populates="client")
  rental: List["Rental"] = Relationship(back_populates="client")


class Staff(SQLModel, table=True):
  staff_id: int = Field(primary_key=True)
  username: str = Field(unique=True)
  full_name: str
  password_hashed: str
  email: str = Field(unique=True) 
  phone: str = Field(unique=True)
  position: UserRole
  
  eventlog: List["EventLog"] = Relationship(back_populates="staff")
  rental: List["Rental"] = Relationship(back_populates="staff")
  refresh_tokens: List["RefreshToken"] = Relationship(back_populates="staff")


class RefreshToken(SQLModel, table=True):
    
    token_id: int = Field(primary_key=True)
    token: str = Field(unique=True, nullable=False)
    staff_id: int = Field(foreign_key="staff.staff_id")
    expires_at: str = Field(nullable=False)
    is_revoked: bool = Field(default=False)
    created_at: datetime = Field(default=datetime.utcnow())

    staff: Optional["Staff"] = Relationship(back_populates="refresh_tokens")



class Cars(SQLModel, table=True):
    car_id: int = Field(primary_key=True)
    number_car: str = Field(unique=True)
    brand: str
    color: str
    year: int
    is_available: CarStatus = Field(default=CarStatus.AVAILABLE)
    category: CarCategory
    daily_price: float

    rental: Optional["Rental"] = Relationship(back_populates="car")
    repair: Optional["Repair"] = Relationship(back_populates="car")



class EventLog(SQLModel, table=True):
  eventLog_id: int = Field(primary_key=True)
  event_time: datetime = Field(default_factory=datetime.now)
  operation: str
  client_id: Optional[int] = Field(foreign_key="client.client_id")
  staff_id: Optional[int] = Field(foreign_key="staff.staff_id")
  description: str


  staff: Optional["Staff"] = Relationship(back_populates="eventlog")
  client: Optional["Client"] = Relationship(back_populates="eventlog")



class Rental(SQLModel, table=True):
  rental_id: int = Field(primary_key=True) # убрать optinal
  client_id: int = Field(foreign_key="client.client_id")
  car_id: int = Field(foreign_key="cars.car_id")
  staff_id: int = Field(foreign_key="staff.staff_id")
  status_rent: RentalStatus
  start_time: datetime # по дефолту постаивть с текущей датой = Field(default_factory=datetime.now)
  end_time: datetime
  total_hours: float
  total_price: float  # рассчет базовая цена делится на 24 и после рассчитывается сколько часов будет в аренде

  client: Optional["Client"] = Relationship(back_populates="rental")
  car: Optional["Cars"] = Relationship(back_populates="rental")
  staff: Optional["Staff"] = Relationship(back_populates="rental")



class Repair(SQLModel, table=True):
  repair_id: int = Field(primary_key=True)
  car_id: int = Field(foreign_key="cars.car_id")
  start_rep: datetime
  end_rep: datetime = Field(default=None, nullable=True)
  price_rep: float

  car: Optional["Cars"] = Relationship(back_populates="repair")



# class TestMigration(SQLModel, table=True):
#     """Тестовая модель для проверки Alembic"""
#     id: Optional[int] = Field(default=None, primary_key=True)
#     name: str = Field(max_length=100)
#     description: Optional[str] = None
#     is_active: bool = Field(default=True)
#     created_at: datetime = Field(default_factory=datetime.utcnow)


# Ref: "client"."client_id" < "EventLog"."client_id"

# Ref: "staff"."staff_id" < "EventLog"."staff_id"

# Ref: "client"."client_id" < "Rental"."client_id"

# Ref: "cars"."car_id" < "Rental"."car_id"

# Ref: "staff"."staff_id" < "Rental"."staff_id"

# Ref: "cars"."car_id" < "Repair"."car_id"
