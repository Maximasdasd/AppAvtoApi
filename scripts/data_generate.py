from faker import Faker
import random
from typing import Optional
from app.models.model import UserRole, CarCategory, CarStatus, RentalStatus
from datetime import datetime, timedelta


fake = Faker()

def generate_client(client_id: Optional[int] = None) -> dict:
    """Генерирует данные клиента (Client)"""
    return {
        "client_id": client_id,
        "full_name": fake.name(),
        "driver_license": f"DL{fake.random_number(digits=6)}",
        "passport": f"{fake.random_number(digits=4)} {fake.random_number(digits=6)}",
        "address": fake.address().replace("\n", ", "),
        "created_at": fake.date_time_this_year(),
        "is_active": random.choice([True, False])
    }

def generate_staff(staff_id: Optional[int] = None) -> dict:
    """Генерирует данные сотрудника (Staff)"""
    positions = list(UserRole)
    return {
        "staff_id": staff_id,
        "username": f"{fake.user_name()}{fake.random_int(100, 999)}",
        "full_name": fake.name(),
        "password_hashed": fake.password(length=12),
        "email": fake.email(),
        "phone": fake.phone_number(),
        "position": random.choice(positions)
    }

def generate_refresh_token(token_id: Optional[int] = None, staff_id: int = None) -> dict:
    """Генерирует токен обновления (RefreshToken)"""
    expires_at = (datetime.utcnow() + timedelta(days=30)).isoformat()
    created_at = datetime.utcnow() - timedelta(hours=random.randint(1, 720))

    return {
        "token_id": token_id,
        "token": fake.uuid4(),
        "staff_id": staff_id,
        "expires_at": expires_at,
        "is_revoked": random.choice([True, False]),
        "created_at": created_at
    }

def generate_car(car_id: Optional[int] = None) -> dict:
    """Генерирует данные автомобиля (Cars)"""
    brands = ['Toyota', 'BMW', 'Audi', 'Mercedes', 'Ford', 'Honda', 'Nissan', 'Volkswagen', 'Lexus', 'Hyundai']
    colors = ['Red', 'Blue', 'Black', 'White', 'Silver', 'Gray', 'Green', 'Yellow', 'Orange', 'Purple']
    categories = list(CarCategory)

    brand = random.choice(brands)
    year = random.randint(2015, 2023)
    daily_price = round(random.uniform(1500, 8000), 2)
    is_available = random.choice(list(CarStatus))

    return {
        "car_id": car_id,
        "number_car": f"{fake.random_letter().upper()}{fake.random_number(digits=3)}{fake.random_letter().upper()*2}{fake.random_number(digits=2)}",
        "brand": brand,
        "color": random.choice(colors),
        "year": year,
        "is_available": is_available,
        "category": random.choice(categories),
        "daily_price": daily_price
    }

def generate_rental(rental_id: Optional[int] = None, client_id: int = None, car_id: int = None, staff_id: int = None) -> dict:
    """Генерирует данные аренды (Rental)"""
    status = random.choice(list(RentalStatus))
    start_time = fake.date_time_this_month()
    duration_days = random.randint(1, 14)
    end_time = start_time + timedelta(days=duration_days)
    total_hours = (end_time - start_time).total_seconds() / 3600  # в часах

    # Расчёт цены: базовая цена за день / 24 * количество часов
    daily_price = random.uniform(1500, 8000)
    hourly_rate = daily_price / 24
    total_price = round(hourly_rate * total_hours, 2)

    return {
        "rental_id": rental_id,
        "client_id": client_id,
        "car_id": car_id,
        "staff_id": staff_id,
        "status_rent": status,
        "start_time": start_time,
        "end_time": end_time,
        "total_hours": total_hours,
        "total_price": total_price
    }

def generate_repair(repair_id: Optional[int] = None, car_id: int = None) -> dict:
    """Генерирует данные о ремонте (Repair)"""
    start_rep = fake.date_time_between(start_date="-60d", end_date="now")
    duration_hours = random.randint(2, 168)  # от 2 часов до 7 дней
    end_rep = start_rep + timedelta(hours=duration_hours) if random.random() > 0.3 else None
    price_rep = round(random.uniform(5000, 50000), 2)

    return {
        "repair_id": repair_id,
        "car_id": car_id,
        "start_rep": start_rep,
        "end_rep": end_rep,
        "price_rep": price_rep
    }