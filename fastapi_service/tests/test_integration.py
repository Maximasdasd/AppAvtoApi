"""
Интеграционные тесты для Car Rental FastAPI сервиса.

Запуск:
    cd fastapi_service
    pytest tests/test_integration.py -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.main import app
from app.db.db import get_db
from app.models.model import Staff, Client, Cars, Rental, Repair
from app.core.security import get_password_hash


# ──────────────────────────────────────────────
# Фикстуры
# ──────────────────────────────────────────────

@pytest.fixture
def db_session():
    """Создаёт тестовую БД SQLite in-memory"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlmodel import SQLModel
    
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    # Переопределяем зависимость БД
    def override_get_db():
        try:
            yield session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield session
    
    session.close()
    app.dependency_overrides.clear()


@pytest.fixture
def client(db_session):
    """TestClient с тестовой БД"""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def auth_headers():
    """Генерирует заголовки с токеном для админа"""
    from jose import jwt
    from datetime import datetime, timedelta, timezone
    
    payload = {
        "sub": "1",
        "roles": ["admin"],
        "type": "access",
        "exp": int((datetime.now(timezone.utc) + timedelta(minutes=30)).timestamp()),
    }
    token = jwt.encode(payload, "test_secret_key_for_tests", algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def manager_headers():
    """Заголовки для менеджера"""
    from jose import jwt
    from datetime import datetime, timedelta, timezone
    
    payload = {
        "sub": "2",
        "roles": ["manager"],
        "type": "access",
        "exp": int((datetime.now(timezone.utc) + timedelta(minutes=30)).timestamp()),
    }
    token = jwt.encode(payload, "test_secret_key_for_tests", algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


# ──────────────────────────────────────────────
# Тесты Staff
# ──────────────────────────────────────────────

class TestStaffIntegration:
    
    def test_create_staff_success(self, client, auth_headers, db_session):
        response = client.post(
            "/staff/create_staff",
            headers=auth_headers,
            json={
                "username": "test_staff",
                "full_name": "Тестовый Сотрудник",
                "email": "test@example.com",
                "phone": "+79001234567",
                "position": "manager",
                "password": "SecurePass123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "test_staff"
        assert data["email"] == "test@example.com"
        
        # Проверяем, что запись действительно в БД
        staff = db_session.exec(select(Staff).where(Staff.username == "test_staff")).first()
        assert staff is not None
        assert staff.full_name == "Тестовый Сотрудник"
    
    def test_create_staff_duplicate_username_409(self, client, auth_headers, db_session):
        # Создаём первого сотрудника
        client.post("/staff/create_staff", headers=auth_headers, json={
            "username": "duplicate_user",
            "full_name": "Первый",
            "email": "first@example.com",
            "phone": "+79001234560",
            "position": "manager",
            "password": "pass123"
        })
        
        # Пытаемся создать второго с тем же username
        response = client.post("/staff/create_staff", headers=auth_headers, json={
            "username": "duplicate_user",
            "full_name": "Второй",
            "email": "second@example.com",
            "phone": "+79001234561",
            "position": "manager",
            "password": "pass123"
        })
        assert response.status_code == 409
        assert "существует" in response.text.lower() or "already" in response.text.lower()
    
    def test_get_staff_by_id_success(self, client, auth_headers, db_session):
        # Создаём сотрудника
        create_resp = client.post("/staff/create_staff", headers=auth_headers, json={
            "username": "get_staff_test",
            "full_name": "Тестовый",
            "email": "get@example.com",
            "phone": "+79001234562",
            "position": "manager",
            "password": "pass123"
        })
        staff_id = create_resp.json()["staff_id"]
        
        # Получаем по ID
        response = client.get(f"/staff/get_staff_by_id/{staff_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["username"] == "get_staff_test"
    
    def test_get_staff_by_id_not_found_404(self, client, auth_headers):
        response = client.get("/staff/get_staff_by_id/99999", headers=auth_headers)
        assert response.status_code == 404
    
    def test_login_success(self, client, db_session):
        # Создаём сотрудника напрямую в БД
        staff = Staff(
            username="login_test",
            full_name="Login Test",
            email="login@example.com",
            phone="+79001234563",
            position="manager",
            password_hashed=get_password_hash("correct_password")
        )
        db_session.add(staff)
        db_session.commit()
        
        response = client.post(
            "/staff/login_staff",
            data={"username": "login_test", "password": "correct_password"}
        )
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert "refresh_token" in response.json()
    
    def test_login_wrong_password_404(self, client, db_session):
        staff = Staff(
            username="wrong_pass_test",
            full_name="Test",
            email="wrong@example.com",
            phone="+79001234564",
            position="manager",
            password_hashed=get_password_hash("real_password")
        )
        db_session.add(staff)
        db_session.commit()
        
        response = client.post(
            "/staff/login_staff",
            data={"username": "wrong_pass_test", "password": "wrong_password"}
        )
        assert response.status_code == 404
    
    def test_login_unknown_user_404(self, client):
        response = client.post(
            "/staff/login_staff",
            data={"username": "nonexistent", "password": "anything"}
        )
        assert response.status_code == 404
    
    def test_info_me_returns_current_user(self, client, auth_headers):
        response = client.get("/staff/info_me", headers=auth_headers)
        assert response.status_code == 200
        assert "sub" in response.json()
    
    def test_info_me_unauthorized_401(self, client):
        response = client.get("/staff/info_me")
        assert response.status_code in (401, 403, 422)


# ──────────────────────────────────────────────
# Тесты Cars
# ──────────────────────────────────────────────

class TestCarIntegration:
    
    def test_create_car_success(self, client, auth_headers, db_session):
        response = client.post(
            "/car/create_car",
            headers=auth_headers,
            json={
                "number_car": "TEST123",
                "brand": "Toyota",
                "model": "Camry",
                "color": "White",
                "year": 2022,
                "category": "ECONOMY",
                "daily_price": 2500.0
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["number_car"] == "TEST123"
        assert data["brand"] == "Toyota"
        assert data["is_available"] == "available"
        
        # Проверяем БД
        car = db_session.exec(select(Cars).where(Cars.number_car == "TEST123")).first()
        assert car is not None
        assert car.brand == "Toyota"
    
    def test_create_car_duplicate_number_409(self, client, auth_headers, db_session):
        # Создаём первую машину
        client.post("/car/create_car", headers=auth_headers, json={
            "number_car": "DUPLICATE",
            "brand": "BMW",
            "model": "X5",
            "color": "Black",
            "year": 2023,
            "category": "PREMIUM",
            "daily_price": 5000.0
        })
        
        # Пытаемся создать с тем же номером
        response = client.post("/car/create_car", headers=auth_headers, json={
            "number_car": "DUPLICATE",
            "brand": "Audi",
            "model": "Q7",
            "color": "White",
            "year": 2023,
            "category": "PREMIUM",
            "daily_price": 5500.0
        })
        assert response.status_code == 409
    
    def test_get_car_by_id_success(self, client, auth_headers, db_session):
        # Создаём машину
        car = Cars(
            number_car="GET123",
            brand="Honda",
            model="Civic",
            color="Red",
            year=2021,
            category="ECONOMY",
            daily_price=2000.0,
            is_available="available"
        )
        db_session.add(car)
        db_session.commit()
        
        response = client.get(f"/car/get_car/{car.car_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["brand"] == "Honda"
        assert response.json()["number_car"] == "GET123"
    
    def test_get_car_not_found_404(self, client, auth_headers):
        response = client.get("/car/get_car/99999", headers=auth_headers)
        assert response.status_code == 404
    
    def test_get_all_cars(self, client, auth_headers, db_session):
        # Добавляем несколько машин
        for i in range(3):
            car = Cars(
                number_car=f"ALL{i}",
                brand=f"Brand{i}",
                model="Model",
                color="Black",
                year=2020,
                category="ECONOMY",
                daily_price=1000.0,
                is_available="available"
            )
            db_session.add(car)
        db_session.commit()
        
        response = client.get("/car/get_cars_all", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 3
    
    def test_delete_car_success(self, client, auth_headers, db_session):
        # Создаём машину
        car = Cars(
            number_car="DELETE123",
            brand="Ford",
            model="Focus",
            color="Blue",
            year=2020,
            category="ECONOMY",
            daily_price=1500.0,
            is_available="available"
        )
        db_session.add(car)
        db_session.commit()
        car_id = car.car_id
        
        response = client.delete(f"/car/delete_car/{car_id}", headers=auth_headers)
        assert response.status_code == 200
        
        # Проверяем, что машины нет в БД
        deleted_car = db_session.exec(select(Cars).where(Cars.car_id == car_id)).first()
        assert deleted_car is None
    
    def test_delete_rented_car_400(self, client, auth_headers, db_session):
        # Создаём машину со статусом "rented"
        car = Cars(
            number_car="RENTED123",
            brand="Tesla",
            model="Model 3",
            color="Red",
            year=2023,
            category="PREMIUM",
            daily_price=8000.0,
            is_available="rented"
        )
        db_session.add(car)
        db_session.commit()
        
        response = client.delete(f"/car/delete_car/{car.car_id}", headers=auth_headers)
        assert response.status_code == 400
        assert "аренде" in response.text.lower() or "rented" in response.text.lower()
    
    def test_delete_car_under_repair_400(self, client, auth_headers, db_session):
        car = Cars(
            number_car="REPAIR123",
            brand="Nissan",
            model="Qashqai",
            color="Silver",
            year=2022,
            category="STANDARD",
            daily_price=3000.0,
            is_available="under_repair"
        )
        db_session.add(car)
        db_session.commit()
        
        response = client.delete(f"/car/delete_car/{car.car_id}", headers=auth_headers)
        assert response.status_code == 400
        assert "ремонт" in response.text.lower() or "repair" in response.text.lower()


# ──────────────────────────────────────────────
# Тесты Client
# ──────────────────────────────────────────────

class TestClientIntegration:
    
    def test_create_client_success(self, client, auth_headers, db_session):
        response = client.post(
            "/client/create_client",
            headers=auth_headers,
            json={
                "full_name": "Клиентов Клиент Клиентович",
                "driver_license": "77АА123456",
                "passport": "4521 123456",
                "address": "г. Москва, ул. Тестовая, д.1"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["full_name"] == "Клиентов Клиент Клиентович"
        assert data["is_active"] is True
        
        # Проверяем БД
        client_db = db_session.exec(select(Client).where(Client.driver_license == "77АА123456")).first()
        assert client_db is not None
    
    def test_create_client_duplicate_driver_license_409(self, client, auth_headers, db_session):
        client.post("/client/create_client", headers=auth_headers, json={
            "full_name": "Первый Клиент",
            "driver_license": "LICENSE123",
            "passport": "1234 567890",
            "address": "Адрес 1"
        })
        
        response = client.post("/client/create_client", headers=auth_headers, json={
            "full_name": "Второй Клиент",
            "driver_license": "LICENSE123",
            "passport": "0987 654321",
            "address": "Адрес 2"
        })
        assert response.status_code == 409
    
    def test_create_client_duplicate_passport_409(self, client, auth_headers, db_session):
        client.post("/client/create_client", headers=auth_headers, json={
            "full_name": "Клиент А",
            "driver_license": "DRV123",
            "passport": "PASSPORT999",
            "address": "Адрес А"
        })
        
        response = client.post("/client/create_client", headers=auth_headers, json={
            "full_name": "Клиент Б",
            "driver_license": "DRV456",
            "passport": "PASSPORT999",
            "address": "Адрес Б"
        })
        assert response.status_code == 409
    
    def test_get_client_by_id_success(self, client, auth_headers, db_session):
        client_db = Client(
            full_name="Для Получения",
            driver_license="GETLICENSE",
            passport="1111 222222",
            address="Адрес",
            is_active=True
        )
        db_session.add(client_db)
        db_session.commit()
        
        response = client.get(f"/client/get_client/{client_db.client_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["full_name"] == "Для Получения"
    
    def test_get_client_not_found_404(self, client, auth_headers):
        response = client.get("/client/get_client/99999", headers=auth_headers)
        assert response.status_code == 404
    
    def test_get_all_clients(self, client, auth_headers, db_session):
        for i in range(3):
            client_db = Client(
                full_name=f"Клиент{i}",
                driver_license=f"LIC{i}",
                passport=f"PASS{i}",
                address=f"Адрес{i}",
                is_active=True
            )
            db_session.add(client_db)
        db_session.commit()
        
        response = client.get("/client/get_clients_all", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 3


# ──────────────────────────────────────────────
# Тесты Rental
# ──────────────────────────────────────────────

class TestRentalIntegration:
    
    @pytest.fixture
    def setup_car_and_client(self, db_session):
        """Создаёт тестовые машину и клиента"""
        car = Cars(
            number_car="RENTCAR",
            brand="RentalCar",
            model="Test",
            color="White",
            year=2022,
            category="ECONOMY",
            daily_price=2000.0,
            is_available="available"
        )
        client = Client(
            full_name="Арендатор",
            driver_license="RENTLIC",
            passport="5555 666666",
            address="Адрес",
            is_active=True
        )
        db_session.add(car)
        db_session.add(client)
        db_session.commit()
        return {"car_id": car.car_id, "client_id": client.client_id}
    
    def test_create_rental_success(self, client, auth_headers, db_session, setup_car_and_client):
        response = client.post(
            "/rental/create_rental",
            headers=auth_headers,
            json={
                "car_id": setup_car_and_client["car_id"],
                "client_id": setup_car_and_client["client_id"],
                "start_time": "2025-06-01T10:00:00",
                "end_time": "2025-06-03T10:00:00"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status_rent"] == "active"
        assert data["total_hours"] == 48
        
        # Проверяем, что статус машины изменился на "rented"
        car = db_session.get(Cars, setup_car_and_client["car_id"])
        assert car.is_available == "rented"
    
    def test_create_rental_car_not_available_400(self, client, auth_headers, db_session, setup_car_and_client):
        # Сначала арендуем машину
        client.post("/rental/create_rental", headers=auth_headers, json={
            "car_id": setup_car_and_client["car_id"],
            "client_id": setup_car_and_client["client_id"],
            "start_time": "2025-06-01T10:00:00",
            "end_time": "2025-06-03T10:00:00"
        })
        
        # Пытаемся арендовать ту же машину снова
        response = client.post("/rental/create_rental", headers=auth_headers, json={
            "car_id": setup_car_and_client["car_id"],
            "client_id": setup_car_and_client["client_id"],
            "start_time": "2025-06-05T10:00:00",
            "end_time": "2025-06-07T10:00:00"
        })
        assert response.status_code == 400
    
    def test_create_rental_car_not_found_404(self, client, auth_headers, setup_car_and_client):
        response = client.post("/rental/create_rental", headers=auth_headers, json={
            "car_id": 99999,
            "client_id": setup_car_and_client["client_id"],
            "start_time": "2025-06-01T10:00:00",
            "end_time": "2025-06-03T10:00:00"
        })
        assert response.status_code == 404
    
    def test_rent_complete_success(self, client, auth_headers, db_session, setup_car_and_client):
        # Создаём аренду
        rent_resp = client.post("/rental/create_rental", headers=auth_headers, json={
            "car_id": setup_car_and_client["car_id"],
            "client_id": setup_car_and_client["client_id"],
            "start_time": "2025-06-01T10:00:00",
            "end_time": "2025-06-03T10:00:00"
        })
        rental_id = rent_resp.json()["rental_id"]
        
        # Завершаем аренду
        response = client.patch(f"/rental/rent_complete?rent_id={rental_id}", headers=auth_headers)
        assert response.status_code == 200
        
        # Проверяем статус аренды
        rental = db_session.get(Rental, rental_id)
        assert rental.status_rent == "completed"
        
        # Проверяем, что машина снова доступна
        car = db_session.get(Cars, setup_car_and_client["car_id"])
        assert car.is_available == "available"
    
    def test_rent_cancel_success(self, client, auth_headers, db_session, setup_car_and_client):
        rent_resp = client.post("/rental/create_rental", headers=auth_headers, json={
            "car_id": setup_car_and_client["car_id"],
            "client_id": setup_car_and_client["client_id"],
            "start_time": "2025-06-01T10:00:00",
            "end_time": "2025-06-03T10:00:00"
        })
        rental_id = rent_resp.json()["rental_id"]
        
        response = client.patch(f"/rental/rent_cancelled?rent_id={rental_id}", headers=auth_headers)
        assert response.status_code == 200
        
        rental = db_session.get(Rental, rental_id)
        assert rental.status_rent == "cancelled"
        
        # Машина должна стать доступной
        car = db_session.get(Cars, setup_car_and_client["car_id"])
        assert car.is_available == "available"
    
    def test_rent_not_found_404(self, client, auth_headers):
        response = client.patch("/rental/rent_complete?rent_id=99999", headers=auth_headers)
        assert response.status_code == 404


# ──────────────────────────────────────────────
# Тесты Repair
# ──────────────────────────────────────────────

class TestRepairIntegration:
    
    @pytest.fixture
    def setup_car(self, db_session):
        car = Cars(
            number_car="REPAIRCAR",
            brand="RepairBrand",
            model="Test",
            color="Black",
            year=2021,
            category="STANDARD",
            daily_price=2500.0,
            is_available="available"
        )
        db_session.add(car)
        db_session.commit()
        return {"car_id": car.car_id}
    
    def test_create_repair_success(self, client, auth_headers, db_session, setup_car):
        response = client.post(
            "/repair/create_repair",
            headers=auth_headers,
            json={
                "car_id": setup_car["car_id"],
                "start_rep": "2025-06-01T09:00:00",
                "price_rep": 15000.0
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["car_id"] == setup_car["car_id"]
        assert data["end_rep"] is None
        
        # Проверяем статус машины
        car = db_session.get(Cars, setup_car["car_id"])
        assert car.is_available == "under_repair"
    
    def test_create_repair_car_not_found_404(self, client, auth_headers):
        response = client.post("/repair/create_repair", headers=auth_headers, json={
            "car_id": 99999,
            "start_rep": "2025-06-01T09:00:00",
            "price_rep": 10000.0
        })
        assert response.status_code == 404
    
    def test_create_repair_car_already_in_repair_400(self, client, auth_headers, db_session, setup_car):
        # Отправляем в ремонт
        client.post("/repair/create_repair", headers=auth_headers, json={
            "car_id": setup_car["car_id"],
            "start_rep": "2025-06-01T09:00:00",
            "price_rep": 10000.0
        })
        
        # Пытаемся снова отправить в ремонт
        response = client.post("/repair/create_repair", headers=auth_headers, json={
            "car_id": setup_car["car_id"],
            "start_rep": "2025-06-02T09:00:00",
            "price_rep": 5000.0
        })
        assert response.status_code == 400
    
    def test_create_repair_negative_price_400(self, client, auth_headers, setup_car):
        response = client.post("/repair/create_repair", headers=auth_headers, json={
            "car_id": setup_car["car_id"],
            "start_rep": "2025-06-01T09:00:00",
            "price_rep": -1000.0
        })
        assert response.status_code == 400
    
    def test_complete_repair_success(self, client, auth_headers, db_session, setup_car):
        # Создаём ремонт
        repair_resp = client.post("/repair/create_repair", headers=auth_headers, json={
            "car_id": setup_car["car_id"],
            "start_rep": "2025-06-01T09:00:00",
            "price_rep": 10000.0
        })
        repair_id = repair_resp.json()["repair_id"]
        
        # Завершаем ремонт
        response = client.patch(
            f"/repair/complete_repair?repair_id={repair_id}",
            headers=auth_headers,
            json={"end_rep": "2025-06-05T17:00:00"}
        )
        assert response.status_code == 200
        
        repair = db_session.get(Repair, repair_id)
        assert repair.end_rep is not None
        
        # Проверяем, что машина стала доступной
        car = db_session.get(Cars, setup_car["car_id"])
        assert car.is_available == "available"
    
    def test_get_repair_by_id_success(self, client, auth_headers, db_session, setup_car):
        repair = Repair(
            car_id=setup_car["car_id"],
            start_rep="2025-06-01T09:00:00",
            price_rep=8000.0
        )
        db_session.add(repair)
        db_session.commit()
        
        response = client.get(f"/repair/get_repair_by_id?repair_id={repair.repair_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["price_rep"] == 8000.0
    
    def test_delete_repair_success(self, client, auth_headers, db_session, setup_car):
        repair = Repair(
            car_id=setup_car["car_id"],
            start_rep="2025-06-01T09:00:00",
            price_rep=5000.0
        )
        db_session.add(repair)
        db_session.commit()
        
        response = client.delete(f"/repair/delete_repair_by_id?repair_id={repair.repair_id}", headers=auth_headers)
        assert response.status_code == 200
        
        deleted = db_session.get(Repair, repair.repair_id)
        assert deleted is None