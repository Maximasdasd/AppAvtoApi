"""
Интеграционные тесты Car Rental API.

Поднимается реальное приложение (main.app) поверх in-memory SQLite.
Проверяются полные цепочки: HTTP-запрос -> роут -> контроллер -> БД ->
обработчики ошибок -> ответ. Авторизация проходит через настоящий JWT
(роль admin) из conftest, поэтому guard'ы ролей тоже реально отрабатывают.

Все тесты в одном файле, фикстуры — в conftest.py.
"""
from datetime import datetime, timedelta, timezone

import pytest

from models.model import Cars, Client, Rental, Repair, CarStatus, RentalStatus


# ====================================================================
#  Корневой endpoint
# ====================================================================
class TestRoot:
    def test_root_ok(self, client):
        r = client.get("/")
        assert r.status_code == 200
        body = r.json()
        assert body["message"] == "Car Rental API"
        assert body["version"] == "1.0.0"


# ====================================================================
#  Авторизация / guard
# ====================================================================
class TestAuthGuard:
    def test_no_token_rejected(self, app):
        """Без переопределения oauth2 защищённый endpoint должен дать 401."""
        from fastapi.testclient import TestClient
        from core.security import oauth2_scheme

        # снимаем подмену токена, оставляя подмену БД
        app.dependency_overrides.pop(oauth2_scheme, None)
        bare = TestClient(app, raise_server_exceptions=False)
        r = bare.get("/car/get_cars_all")
        assert r.status_code in (401, 403)


# ====================================================================
#  /car
# ====================================================================
class TestCar:
    def test_create_car(self, client):
        payload = {
            "number_car": "X777XX",
            "brand": "BMW",
            "color": "white",
            "year": 2022,
            "category": "PREMIUM",
            "daily_price": 5000.0,
        }
        r = client.post("/car/create_car", json=payload)
        assert r.status_code == 201
        data = r.json()
        assert data["number_car"] == "X777XX"
        assert data["is_available"] == "available"
        assert "car_id" in data

    def test_create_car_duplicate_number(self, client, sample_car):
        payload = {
            "number_car": sample_car.number_car,  # уже существует
            "brand": "Audi",
            "color": "red",
            "year": 2021,
            "category": "STANDARD",
            "daily_price": 3000.0,
        }
        r = client.post("/car/create_car", json=payload)
        assert r.status_code == 409

    def test_create_car_bad_category(self, client):
        payload = {
            "number_car": "Y111YY",
            "brand": "Lada",
            "color": "grey",
            "year": 2019,
            "category": "SUPER_LUX",  # нет такой категории
            "daily_price": 1000.0,
        }
        r = client.post("/car/create_car", json=payload)
        assert r.status_code == 422

    def test_create_car_missing_field(self, client):
        payload = {"brand": "Kia", "color": "blue"}  # нет number_car, year и т.д.
        r = client.post("/car/create_car", json=payload)
        assert r.status_code == 422

    def test_get_car_by_id(self, client, sample_car):
        r = client.get(f"/car/get_car/{sample_car.car_id}")
        assert r.status_code == 200
        assert r.json()["car_id"] == sample_car.car_id

    def test_get_car_not_found(self, client):
        r = client.get("/car/get_car/999999")
        assert r.status_code == 404

    def test_get_cars_all_paginated(self, client, sample_car):
        r = client.get("/car/get_cars_all")
        assert r.status_code == 200
        body = r.json()
        assert "items" in body and "total" in body
        assert body["total"] >= 1

    def test_delete_car(self, client, sample_car):
        r = client.delete(f"/car/delete_car/{sample_car.car_id}")
        assert r.status_code == 200
        # повторное получение — 404
        r2 = client.get(f"/car/get_car/{sample_car.car_id}")
        assert r2.status_code == 404

    def test_delete_rented_car_forbidden(self, client, db_session, sample_car):
        sample_car.is_available = CarStatus.RENTED
        db_session.add(sample_car)
        db_session.commit()
        r = client.delete(f"/car/delete_car/{sample_car.car_id}")
        assert r.status_code == 400


# ====================================================================
#  /client
# ====================================================================
class TestClient:
    def _payload(self, **over):
        base = {
            "full_name": "Пётр Петров",
            "driver_license": "7654321",
            "passport": "4600999888",
            "address": "Санкт-Петербург",
        }
        base.update(over)
        return base

    def test_create_client(self, client):
        r = client.post("/client/create_client", json=self._payload())
        assert r.status_code == 201
        data = r.json()
        assert data["full_name"] == "Пётр Петров"
        assert data["is_active"] is True
        assert "client_id" in data

    def test_create_client_duplicate_license(self, client, sample_client):
        r = client.post(
            "/client/create_client",
            json=self._payload(driver_license=sample_client.driver_license,
                               passport="9999999999"),
        )
        assert r.status_code == 409

    def test_create_client_short_license(self, client):
        # driver_license min_length=5
        r = client.post("/client/create_client", json=self._payload(driver_license="12"))
        assert r.status_code == 422

    def test_get_client_by_id(self, client, sample_client):
        r = client.get(f"/client/get_client/{sample_client.client_id}")
        assert r.status_code == 200
        assert r.json()["client_id"] == sample_client.client_id

    def test_get_client_not_found(self, client):
        r = client.get("/client/get_client/999999")
        assert r.status_code == 404

    def test_get_clients_all_paginated(self, client, sample_client):
        r = client.get("/client/get_clients_all")
        assert r.status_code == 200
        assert r.json()["total"] >= 1


# ====================================================================
#  /staff
# ====================================================================
class TestStaff:
    def _payload(self, **over):
        base = {
            "username": "manager1",
            "full_name": "Менеджер Один",
            "email": "m1@test.com",
            "phone": "+71112223344",
            "position": "manager",
            "password": "secret123",
        }
        base.update(over)
        return base

    def test_create_staff(self, client, admin_staff):
        r = client.post("/staff/create_staff", json=self._payload())
        assert r.status_code == 200
        data = r.json()
        assert data["username"] == "manager1"
        assert "staff_id" in data
        assert "password" not in data  # пароль не должен утекать

    def test_create_staff_duplicate_username(self, client, admin_staff):
        r = client.post("/staff/create_staff", json=self._payload(username=admin_staff.username))
        assert r.status_code == 409

    def test_create_staff_bad_role(self, client, admin_staff):
        r = client.post("/staff/create_staff", json=self._payload(position="superhero"))
        assert r.status_code == 422

    def test_get_staff_by_id(self, client, admin_staff):
        r = client.get(f"/staff/get_staff_by_id/{admin_staff.staff_id}")
        assert r.status_code == 200
        assert r.json()["staff_id"] == admin_staff.staff_id

    def test_get_staff_not_found(self, client, admin_staff):
        r = client.get("/staff/get_staff_by_id/999999")
        assert r.status_code == 404

    def test_login_success(self, client, admin_staff):
        r = client.post(
            "/staff/login_staff",
            data={"username": "qweqwe", "password": "qwerty"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["token_type"] == "bearer"
        assert body["access_token"]
        assert body["refresh_token"]

    def test_login_wrong_password(self, client, admin_staff):
        r = client.post(
            "/staff/login_staff",
            data={"username": "qweqwe", "password": "wrong"},
        )
        assert r.status_code == 404

    def test_login_unknown_user(self, client):
        r = client.post(
            "/staff/login_staff",
            data={"username": "nobody", "password": "x"},
        )
        assert r.status_code == 404

    def test_info_me(self, client, admin_staff):
        r = client.get("/staff/info_me")
        assert r.status_code == 200
        assert r.json()["sub"] == "qweqwe"


# ====================================================================
#  /rental
# ====================================================================
class TestRental:
    def _rent_payload(self, client_id, car_id):
        start = datetime.now(timezone.utc)
        end = start + timedelta(hours=5)
        return {
            "client_id": client_id,
            "car_id": car_id,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        }

    def test_create_rental(self, client, db_session, admin_staff, sample_car, sample_client):
        r = client.post(
            "/rental/create_rental",
            json=self._rent_payload(sample_client.client_id, sample_car.car_id),
        )
        assert r.status_code == 201
        data = r.json()
        assert data["status_rent"] == "active"
        assert data["car_id"] == sample_car.car_id
        # машина должна стать арендованной
        db_session.expire_all()
        car = db_session.get(Cars, sample_car.car_id)
        assert car.is_available == CarStatus.RENTED

    def test_create_rental_car_busy(self, client, db_session, admin_staff, sample_car, sample_client):
        sample_car.is_available = CarStatus.RENTED
        db_session.add(sample_car)
        db_session.commit()
        r = client.post(
            "/rental/create_rental",
            json=self._rent_payload(sample_client.client_id, sample_car.car_id),
        )
        assert r.status_code == 400

    def test_create_rental_end_before_start(self, client, admin_staff, sample_car, sample_client):
        start = datetime.now(timezone.utc)
        end = start - timedelta(hours=2)
        payload = {
            "client_id": sample_client.client_id,
            "car_id": sample_car.car_id,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        }
        r = client.post("/rental/create_rental", json=payload)
        assert r.status_code == 400

    def test_get_rental_all(self, client, db_session, admin_staff, sample_car, sample_client):
        client.post("/rental/create_rental",
                    json=self._rent_payload(sample_client.client_id, sample_car.car_id))
        r = client.get("/rental/get_rental_all")
        assert r.status_code == 200
        assert r.json()["total"] >= 1

    def test_rent_complete(self, client, db_session, admin_staff, sample_car, sample_client):
        cr = client.post("/rental/create_rental",
                         json=self._rent_payload(sample_client.client_id, sample_car.car_id))
        rent_id = cr.json()["rental_id"]
        r = client.patch(f"/rental/rent_complete?rent_id={rent_id}")
        assert r.status_code == 200
        assert r.json()["status"] == RentalStatus.COMPLETED.value

    def test_rent_cancel(self, client, db_session, admin_staff, sample_car, sample_client):
        cr = client.post("/rental/create_rental",
                         json=self._rent_payload(sample_client.client_id, sample_car.car_id))
        rent_id = cr.json()["rental_id"]
        r = client.patch(f"/rental/rent_cancelled?rent_id={rent_id}")
        assert r.status_code == 200
        assert r.json()["status"] == RentalStatus.CANCELLED.value

    def test_rent_complete_not_found(self, client, admin_staff):
        r = client.patch("/rental/rent_complete?rent_id=999999")
        assert r.status_code == 404

    def test_get_rent_by_status(self, client, db_session, admin_staff, sample_car, sample_client):
        client.post("/rental/create_rental",
                    json=self._rent_payload(sample_client.client_id, sample_car.car_id))
        r = client.get("/rental/get_rent_by_status?status_rent=ACTIVE")
        assert r.status_code == 200
        assert r.json()["total"] >= 1


# ====================================================================
#  /repair
# ====================================================================
class TestRepair:
    def _repair_payload(self, car_id, **over):
        base = {
            "car_id": car_id,
            "start_rep": datetime.now(timezone.utc).isoformat(),
            "price_rep": 1500.0,
        }
        base.update(over)
        return base

    def test_create_repair(self, client, db_session, admin_staff, sample_car):
        r = client.post("/repair/create_repair", json=self._repair_payload(sample_car.car_id))
        assert r.status_code == 201
        data = r.json()
        assert data["car_id"] == sample_car.car_id
        db_session.expire_all()
        car = db_session.get(Cars, sample_car.car_id)
        assert car.is_available == CarStatus.UNDER_REPAIR

    def test_create_repair_car_not_found(self, client, admin_staff):
        r = client.post("/repair/create_repair", json=self._repair_payload(999999))
        assert r.status_code == 404

    def test_create_repair_negative_price(self, client, admin_staff, sample_car):
        r = client.post("/repair/create_repair",
                        json=self._repair_payload(sample_car.car_id, price_rep=-100.0))
        assert r.status_code == 400

    def test_create_repair_already_in_repair(self, client, db_session, admin_staff, sample_car):
        sample_car.is_available = CarStatus.UNDER_REPAIR
        db_session.add(sample_car)
        db_session.commit()
        r = client.post("/repair/create_repair", json=self._repair_payload(sample_car.car_id))
        assert r.status_code == 400

    def test_get_repair_all(self, client, admin_staff, sample_car):
        client.post("/repair/create_repair", json=self._repair_payload(sample_car.car_id))
        r = client.get("/repair/get_repair_all")
        assert r.status_code == 200
        assert r.json()["total"] >= 1

    def test_get_repair_by_id(self, client, admin_staff, sample_car):
        cr = client.post("/repair/create_repair", json=self._repair_payload(sample_car.car_id))
        repair_id = cr.json()["repair_id"]
        r = client.get(f"/repair/get_repair_by_id?repair_id={repair_id}")
        assert r.status_code == 200
        assert r.json()["repair_id"] == repair_id

    def test_get_repair_by_id_not_found(self, client, admin_staff):
        r = client.get("/repair/get_repair_by_id?repair_id=999999")
        assert r.status_code == 404

    def test_complete_repair(self, client, db_session, admin_staff, sample_car):
        cr = client.post("/repair/create_repair", json=self._repair_payload(sample_car.car_id))
        repair_id = cr.json()["repair_id"]
        end = (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat()
        r = client.patch(
            f"/repair/complete_repair?repair_id={repair_id}",
            json={"end_rep": end},
        )
        assert r.status_code == 200
        db_session.expire_all()
        car = db_session.get(Cars, sample_car.car_id)
        assert car.is_available == CarStatus.AVAILABLE

    def test_delete_repair_by_id(self, client, admin_staff, sample_car):
        cr = client.post("/repair/create_repair", json=self._repair_payload(sample_car.car_id))
        repair_id = cr.json()["repair_id"]
        r = client.delete(f"/repair/delete_repair_by_id?repair_id={repair_id}")
        assert r.status_code == 200
