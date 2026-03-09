
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from sqlalchemy import create_engine
from app.models.model import Client, Staff, RefreshToken, Cars, Rental, Repair
from scripts.data_generate import (
    generate_client, generate_staff, generate_refresh_token,
    generate_car, generate_rental, generate_repair
)
import random

engine = create_engine(settings.get_database_url())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_database():
    db = SessionLocal()
    try:
        db.query(Rental).delete()
        db.query(Repair).delete()
        db.query(RefreshToken).delete()
        db.query(Cars).delete()
        db.query(Staff).delete()
        db.query(Client).delete()
        db.commit()
        # Генерируем 10 клиентов
        clients = []
        for i in range(10):
            client_data = generate_client(client_id=i + 1)
            client = Client(**client_data)
            db.add(client)
            clients.append(client)
        db.commit()

        # Генерируем 5 сотрудников
        staffs = []
        for i in range(5):
            staff_data = generate_staff(staff_id=i + 1)
            staff = Staff(**staff_data)
            db.add(staff)
            staffs.append(staff)
        db.commit()

        # Генерируем токены для сотрудников
        for staff in staffs:
            token_data = generate_refresh_token(staff_id=staff.staff_id)
            token = RefreshToken(**token_data)
            db.add(token)
        db.commit()

        # Генерируем 8 автомобилей
        cars = []
        for i in range(8):
            car_data = generate_car(car_id=i + 1)
            car = Cars(**car_data)
            db.add(car)
            cars.append(car)
        db.commit()

        # Генерируем аренды (случайные комбинации)
        for _ in range(15):
            client = random.choice(clients)
            car = random.choice(cars)
            staff = random.choice(staffs)
            rental_data = generate_rental(
                client_id=client.client_id,
                car_id=car.car_id,
                staff_id=staff.staff_id
            )
            rental = Rental(**rental_data)
            db.add(rental)
        db.commit()

        for car in cars:
            if random.random() > 0.4:  # 60 % вероятность ремонта
                repair_data = generate_repair(car_id=car.car_id)
                repair = Repair(**repair_data)
                db.add(repair)
        db.commit()

        print("База данных успешно заполнена фейковыми данными!")
        print(f"Создано: {len(clients)} клиентов, {len(staffs)} сотрудников, {len(cars)} автомобилей")
        print(f"Создано: {15} аренд, {sum(1 for _ in cars if random.random() > 0.4)} ремонтов")

    except Exception as e:
        print(f"Ошибка при заполнении базы данных: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()