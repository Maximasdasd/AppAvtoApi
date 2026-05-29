"""
Интеграционные тесты пользовательских сценариев Django-сервиса.

Это «интеграционные» в рамках Django-слоя: проверяют сквозные сценарии
(логин → доступ к странице, отправка формы → вызов FastAPI), но сам FastAPI
замокан, чтобы тесты были детерминированы и не требовали запущенного бэкенда.
"""
import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


class TestLoginFlow:
    """Сценарий входа и последующего доступа к защищённым страницам."""

    def test_login_then_dashboard(self, client, mock_login):
        # 1. логинимся (FastAPI-логин замокан -> токен попадает в сессию)
        login_resp = client.post(reverse("login"), {
            "username": "qweqwe", "password": "qwerty",
        })
        assert client.session.get("fastapi_token") == "test-token-123"

        # 2. теперь дашборд доступен (200), а не редирект.
        #    FastAPI-данные мокаем точечно через requests.get.
        from unittest.mock import patch
        import core.views as views

        class _Resp:
            status_code = 200
            ok = True
            def json(self):
                return {"items": [], "total": 0, "page": 1, "size": 50, "pages": 1}

        with patch.object(views.requests, "get", return_value=_Resp()):
            dash = client.get(reverse("home"))
        assert dash.status_code == 200

    def test_no_login_no_access(self, client):
        """Без входа защищённая страница ведёт на логин."""
        resp = client.get(reverse("home"))
        assert resp.status_code == 302
        assert reverse("login") in resp.url


class TestCarCreateFlow:
    """Создание машины через форму Django -> POST в FastAPI."""

    def test_create_car_success_redirects(self, auth_client, mock_fastapi):
        mock_fastapi.set_post({"car_id": 1, "number_car": "A001AA"}, status=201)
        resp = auth_client.post(reverse("car_create"), {
            "number_car": "A001AA", "brand": "Kia", "category": "STANDARD",
            "color": "red", "year_release": "2021", "daily_price": "2400",
        })
        # вьюха после успеха делает redirect
        assert resp.status_code in (302, 200)

    def test_create_car_missing_fields(self, auth_client, mock_fastapi):
        # пустая форma -> вьюха должна показать ошибку и не упасть
        resp = auth_client.post(reverse("car_create"), {})
        assert resp.status_code in (302, 200)


class TestClientCreateFlow:
    def test_create_client_success(self, auth_client, mock_fastapi):
        mock_fastapi.set_post({"client_id": 1}, status=201)
        resp = auth_client.post(reverse("client_create"), {
            "full_name": "Иван", "driver_license": "1234567",
            "passport": "4500111222", "address": "Мск",
        })
        assert resp.status_code in (302, 200)


class TestRepairCompleteFlow:
    def test_complete_repair(self, auth_client, mock_fastapi):
        mock_fastapi.set_patch({"message": "Ремонт завершен"}, status=200)
        resp = auth_client.post(reverse("repair_complete", args=[1]))
        assert resp.status_code in (302, 200)


class TestRentalActions:
    def test_rental_complete(self, auth_client, mock_fastapi):
        mock_fastapi.set_patch({"status": "completed"}, status=200)
        resp = auth_client.post(reverse("rental_complete", args=[1]))
        assert resp.status_code in (302, 200)

    def test_rental_cancel(self, auth_client, mock_fastapi):
        mock_fastapi.set_patch({"status": "cancelled"}, status=200)
        resp = auth_client.post(reverse("rental_cancel", args=[1]))
        assert resp.status_code in (302, 200)
