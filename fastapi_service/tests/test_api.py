"""
Юнит-тесты для Car Rental FastAPI сервиса.

Запуск:
    pip install pytest httpx python-jose bcrypt fastapi sqlmodel fastapi-pagination
    cd fastapi_service
    pytest tests/test_api.py -v
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


# ──────────────────────────────────────────────
# JWT-хелпер
# ──────────────────────────────────────────────

def make_access_token(role: str = "admin") -> str:
    from jose import jwt
    from datetime import datetime, timedelta, timezone
    payload = {
        "sub": "1",
        "roles": [role],
        "type": "access",
        "exp": int((datetime.now(timezone.utc) + timedelta(minutes=30)).timestamp()),
    }
    return jwt.encode(payload, "test_secret_key_for_tests", algorithm="HS256")


# ──────────────────────────────────────────────
# Фикстура: TestClient с замоканными зависимостями
# ──────────────────────────────────────────────

@pytest.fixture()
def app_client():
    """
    Каждый тест получает свежий TestClient и свежие моки контроллеров.
    Пагинируемые эндпоинты мокаются на уровне контроллера — возвращают
    уже готовый объект Page, чтобы не трогать реальную БД.
    """
    from main import app
    from core.security import oauth2_scheme, wrapprer_check_roles
    from dependencies.car import get_controllers
    from dependencies.client import get_controllers_client
    from dependencies.rental import get_controllers_rental
    from dependencies.repair import get_controllers_repair
    from dependencies.staff import get_controllers_staff

    token = make_access_token("admin")

    car_ctrl    = MagicMock()
    client_ctrl = MagicMock()
    rental_ctrl = MagicMock()
    repair_ctrl = MagicMock()
    staff_ctrl  = MagicMock()

    app.dependency_overrides[oauth2_scheme]                             = lambda: token
    app.dependency_overrides[wrapprer_check_roles(["admin"])]           = lambda: True
    app.dependency_overrides[wrapprer_check_roles(["admin", "manager"])]= lambda: True
    app.dependency_overrides[get_controllers]        = lambda: car_ctrl
    app.dependency_overrides[get_controllers_client] = lambda: client_ctrl
    app.dependency_overrides[get_controllers_rental] = lambda: rental_ctrl
    app.dependency_overrides[get_controllers_repair] = lambda: repair_ctrl
    app.dependency_overrides[get_controllers_staff]  = lambda: staff_ctrl

    with TestClient(app, raise_server_exceptions=False) as c:
        c.car_ctrl    = car_ctrl
        c.client_ctrl = client_ctrl
        c.rental_ctrl = rental_ctrl
        c.repair_ctrl = repair_ctrl
        c.staff_ctrl  = staff_ctrl
        yield c

    app.dependency_overrides.clear()


def make_page(items: list) -> dict:
    """Возвращает структуру Page, совместимую с fastapi-pagination."""
    return {"items": items, "total": len(items), "page": 1, "size": 50, "pages": 1}


# ──────────────────────────────────────────────
# Тесты security.py (без HTTP)
# ──────────────────────────────────────────────

class TestSecurity:

    def test_hash_returns_string(self):
        from core.security import get_password_hash
        assert isinstance(get_password_hash("pass123"), str)

    def test_hash_not_plaintext(self):
        from core.security import get_password_hash
        assert get_password_hash("pass123") != "pass123"

    def test_verify_correct_password(self):
        from core.security import get_password_hash, verify_password
        h = get_password_hash("secret")
        assert verify_password("secret", h) is True

    def test_verify_wrong_password(self):
        from core.security import get_password_hash, verify_password
        h = get_password_hash("secret")
        assert verify_password("wrong", h) is False

    def test_access_token_has_roles(self):
        from core.security import create_access_token
        from jose import jwt
        token = create_access_token({"sub": "42"}, roles=["admin"])
        payload = jwt.decode(token, "test_secret_key_for_tests", algorithms=["HS256"])
        assert payload["roles"] == ["admin"]
        assert payload["type"] == "access"

    def test_refresh_token_type(self):
        from core.security import create_refresh_token
        from jose import jwt
        token = create_refresh_token({"sub": "42"})
        payload = jwt.decode(token, "test_secret_key_for_tests", algorithms=["HS256"])
        assert payload["type"] == "refresh"

    def test_decode_invalid_token_raises_401(self):
        from fastapi import HTTPException
        from core.security import decode_token
        with pytest.raises(HTTPException) as exc:
            decode_token("not_a_real_token")
        assert exc.value.status_code == 401

    def test_decode_valid_token(self):
        from jose import jwt
        from core.security import decode_token
        token = jwt.encode({"sub": "7", "type": "access"}, "test_secret_key_for_tests", algorithm="HS256")
        result = decode_token(token)
        assert result["sub"] == "7"


# ──────────────────────────────────────────────
# Root
# ──────────────────────────────────────────────

class TestRoot:

    def test_root_status_200(self, app_client):
        assert app_client.get("/").status_code == 200

    def test_root_body(self, app_client):
        data = app_client.get("/").json()
        assert data["message"] == "Car Rental API"
        assert data["version"] == "1.0.0"


# ──────────────────────────────────────────────
# /car
# Важно: маршруты /get_car/{id} и /delete_car/{id}
# используют path-параметр {id}, но в функции он называется car_id —
# FastAPI биндит по позиции, поэтому передаём /get_car/1 (не ?car_id=1)
# ──────────────────────────────────────────────

CAR_RESPONSE = {
    "car_id": 1, "number_car": "A123BC777", "brand": "Toyota",
    "color": "White", "year": 2022, "category": "ECONOMY",
    "daily_price": 2500.0, "is_available": "available",
}
CAR_PAYLOAD = {k: v for k, v in CAR_RESPONSE.items() if k not in ("car_id", "is_available")}


class TestCarEndpoints:

    def test_create_car_201(self, app_client):
        app_client.car_ctrl.create_car.return_value = CAR_RESPONSE
        resp = app_client.post("/car/create_car", json=CAR_PAYLOAD)
        assert resp.status_code == 201

    def test_create_car_calls_controller(self, app_client):
        app_client.car_ctrl.create_car.return_value = CAR_RESPONSE
        app_client.post("/car/create_car", json=CAR_PAYLOAD)
        app_client.car_ctrl.create_car.assert_called_once()

    def test_create_car_response_fields(self, app_client):
        app_client.car_ctrl.create_car.return_value = CAR_RESPONSE
        data = app_client.post("/car/create_car", json=CAR_PAYLOAD).json()
        assert data["brand"] == "Toyota"
        assert data["car_id"] == 1

    def test_get_car_by_id(self, app_client):
        app_client.car_ctrl.get_car_by_id.return_value = CAR_RESPONSE
        resp = app_client.get("/car/get_car/1")   # path param {id}
        assert resp.status_code == 200

    def test_delete_car(self, app_client):
        app_client.car_ctrl.delete_car.return_value = {"detail": "Deleted"}
        resp = app_client.delete("/car/delete_car/1")   # path param {id}
        assert resp.status_code == 200

    def test_create_car_invalid_category_422(self, app_client):
        resp = app_client.post("/car/create_car", json={**CAR_PAYLOAD, "category": "WRONG"})
        assert resp.status_code == 422

    def test_create_car_missing_brand_422(self, app_client):
        payload = {k: v for k, v in CAR_PAYLOAD.items() if k != "brand"}
        resp = app_client.post("/car/create_car", json=payload)
        assert resp.status_code == 422


# ──────────────────────────────────────────────
# /client
# ──────────────────────────────────────────────

CLIENT_RESPONSE = {
    "client_id": 1, "full_name": "Иванов Иван", "driver_license": "77АА12345",
    "passport": "4521 123456", "address": "Москва", "created_at": "2024-01-15 12:00",
    "is_active": True,
}
CLIENT_PAYLOAD = {k: v for k, v in CLIENT_RESPONSE.items()
                  if k not in ("client_id", "created_at", "is_active")}


class TestClientEndpoints:

    def test_create_client_201(self, app_client):
        app_client.client_ctrl.create_client.return_value = CLIENT_RESPONSE
        assert app_client.post("/client/create_client", json=CLIENT_PAYLOAD).status_code == 201

    def test_create_client_calls_controller(self, app_client):
        app_client.client_ctrl.create_client.return_value = CLIENT_RESPONSE
        app_client.post("/client/create_client", json=CLIENT_PAYLOAD)
        app_client.client_ctrl.create_client.assert_called_once()

    def test_get_client_found(self, app_client):
        app_client.client_ctrl.get_client_by_id.return_value = CLIENT_RESPONSE
        assert app_client.get("/client/get_client/1").status_code == 200

    def test_get_client_not_found_404(self, app_client):
        app_client.client_ctrl.get_client_by_id.return_value = None
        assert app_client.get("/client/get_client/9999").status_code == 404

    def test_driver_license_too_short_422(self, app_client):
        resp = app_client.post("/client/create_client", json={**CLIENT_PAYLOAD, "driver_license": "AB"})
        assert resp.status_code == 422

    def test_driver_license_too_long_422(self, app_client):
        resp = app_client.post("/client/create_client", json={**CLIENT_PAYLOAD, "driver_license": "A" * 20})
        assert resp.status_code == 422


# ──────────────────────────────────────────────
# /staff
# ──────────────────────────────────────────────

STAFF_RESPONSE = {
    "staff_id": 1, "username": "ivanov_m", "full_name": "Иванов Менеджер",
    "email": "manager@example.com", "phone": "+79001234567", "position": "manager",
}
STAFF_PAYLOAD = {**{k: v for k, v in STAFF_RESPONSE.items() if k != "staff_id"}, "password": "Pass1234"}


class TestStaffEndpoints:

    def test_create_staff_200(self, app_client):
        app_client.staff_ctrl.create_staff.return_value = STAFF_RESPONSE
        assert app_client.post("/staff/create_staff", json=STAFF_PAYLOAD).status_code == 200

    def test_create_staff_calls_controller(self, app_client):
        app_client.staff_ctrl.create_staff.return_value = STAFF_RESPONSE
        app_client.post("/staff/create_staff", json=STAFF_PAYLOAD)
        app_client.staff_ctrl.create_staff.assert_called_once()

    def test_get_staff_by_id_found(self, app_client):
        app_client.staff_ctrl.get_staff_by_id.return_value = STAFF_RESPONSE
        resp = app_client.get("/staff/get_staff_by_id/1")
        assert resp.status_code == 200

    def test_get_staff_by_id_not_found_404(self, app_client):
        app_client.staff_ctrl.get_staff_by_id.return_value = None
        assert app_client.get("/staff/get_staff_by_id/9999").status_code == 404

    def test_login_returns_tokens(self, app_client):
        app_client.staff_ctrl.login_staff.return_value = {
            "access_token": "acc", "refresh_token": "ref", "token_type": "bearer",
        }
        resp = app_client.post("/staff/login_staff",
                               data={"username": "ivanov_m", "password": "Pass1234"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_info_me(self, app_client):
        app_client.staff_ctrl.info_me.return_value = {"sub": "1", "roles": ["admin"]}
        assert app_client.get("/staff/info_me").status_code == 200

    def test_invalid_position_422(self, app_client):
        resp = app_client.post("/staff/create_staff", json={**STAFF_PAYLOAD, "position": "ghost"})
        assert resp.status_code == 422


# ──────────────────────────────────────────────
# /rental
# Paginated эндпоинты: контроллер возвращает make_page(),
# который fastapi-pagination сериализует без обращения к БД
# ──────────────────────────────────────────────

RENTAL_RESPONSE = {
    "rental_id": 1, "client_id": 1, "car_id": 1, "staff_id": 1,
    "status_rent": "active", "start_time": "2024-06-01T10:00:00",
    "end_time": "2024-06-03T10:00:00", "total_hours": 48, "total_price": 5000.0,
}
RENTAL_PAYLOAD = {k: v for k, v in RENTAL_RESPONSE.items()
                  if k not in ("rental_id", "staff_id", "status_rent", "total_hours", "total_price")}


class TestRentalEndpoints:

    def test_create_rental_201(self, app_client):
        app_client.rental_ctrl.create_rent.return_value = RENTAL_RESPONSE
        assert app_client.post("/rental/create_rental", json=RENTAL_PAYLOAD).status_code == 201

    def test_get_all_rentals(self, app_client):
        app_client.rental_ctrl.get_all_rent.return_value = make_page([RENTAL_RESPONSE])
        resp = app_client.get("/rental/get_rental_all")
        assert resp.status_code == 200

    def test_rent_cancelled(self, app_client):
        app_client.rental_ctrl.rent_cancelled.return_value = {"detail": "Cancelled"}
        resp = app_client.patch("/rental/rent_cancelled?rent_id=1")
        assert resp.status_code == 200
        app_client.rental_ctrl.rent_cancelled.assert_called_with(1)

    def test_rent_complete(self, app_client):
        app_client.rental_ctrl.rent_complete.return_value = {"detail": "Completed"}
        resp = app_client.patch("/rental/rent_complete?rent_id=1")
        assert resp.status_code == 200
        app_client.rental_ctrl.rent_complete.assert_called_with(1)

    def test_get_rent_by_id(self, app_client):
        app_client.rental_ctrl.get_rent_by_id.return_value = RENTAL_RESPONSE
        assert app_client.get("/rental/get_rent_by_id?rent_id=1").status_code == 200

    def test_get_rent_by_status(self, app_client):
        app_client.rental_ctrl.get_rent_by_status.return_value = make_page([RENTAL_RESPONSE])
        resp = app_client.get("/rental/get_rent_by_status?status_rent=active")
        assert resp.status_code == 200

    def test_clear_list_rent(self, app_client):
        app_client.rental_ctrl.clear_list_rent.return_value = {"deleted": 1}
        assert app_client.delete("/rental/clear_list_rent").status_code == 200


# ──────────────────────────────────────────────
# /repair
# ──────────────────────────────────────────────

REPAIR_RESPONSE = {
    "repair_id": 1, "car_id": 1,
    "start_rep": "2024-06-01T09:00:00", "end_rep": None, "price_rep": 15000.0,
}
REPAIR_PAYLOAD = {k: v for k, v in REPAIR_RESPONSE.items()
                  if k not in ("repair_id", "end_rep")}


class TestRepairEndpoints:

    def test_create_repair_201(self, app_client):
        app_client.repair_ctrl.create_repair.return_value = REPAIR_RESPONSE
        assert app_client.post("/repair/create_repair", json=REPAIR_PAYLOAD).status_code == 201

    def test_get_all_repairs(self, app_client):
        app_client.repair_ctrl.get_repair_all.return_value = make_page([REPAIR_RESPONSE])
        assert app_client.get("/repair/get_repair_all").status_code == 200

    def test_get_repair_by_id(self, app_client):
        app_client.repair_ctrl.get_repair_by_id.return_value = REPAIR_RESPONSE
        assert app_client.get("/repair/get_repair_by_id?repair_id=1").status_code == 200

    def test_complete_repair(self, app_client):
        app_client.repair_ctrl.return_repair.return_value = {
            **REPAIR_RESPONSE, "end_rep": "2024-06-05T17:00:00"
        }
        resp = app_client.patch("/repair/complete_repair?repair_id=1",
                                json={"end_rep": "2024-06-05T17:00:00"})
        assert resp.status_code == 200

    def test_delete_repair_by_id(self, app_client):
        app_client.repair_ctrl.delete_repair_by_id.return_value = {"detail": "Deleted"}
        assert app_client.delete("/repair/delete_repair_by_id?repair_id=1").status_code == 200

    def test_delete_all_repairs(self, app_client):
        app_client.repair_ctrl.delete_repair_all.return_value = {"deleted": 5}
        assert app_client.delete("/repair/all_delete_repair").status_code == 200

    def test_create_repair_missing_car_id_422(self, app_client):
        payload = {k: v for k, v in REPAIR_PAYLOAD.items() if k != "car_id"}
        assert app_client.post("/repair/create_repair", json=payload).status_code == 422


# ──────────────────────────────────────────────
# Auth guard
# ──────────────────────────────────────────────

class TestAuthProtection:

    def test_no_token_returns_401_or_422(self):
        """Запрос без токена — без override зависимостей"""
        from main import app
        # Убеждаемся что нет override
        app.dependency_overrides.clear()
        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.get("/car/get_cars_all")
            assert resp.status_code in (401, 403, 422)
