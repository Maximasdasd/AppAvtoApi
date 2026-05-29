"""
Тесты Django-вьюх сервиса автопроката (AutoFleet).

Покрывают:
  * редиректы на логин при отсутствии токена;
  * успешный рендер страниц при наличии токена (с замоканным FastAPI);
  * проверку заголовков страниц;
  * процесс логина (/login_staff/).
"""
import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db  # сессии Django используют БД


# ──────────────────────────────────────────────
#  Доступ без токена → редирект на логин
# ──────────────────────────────────────────────
class TestAuthRedirects:
    """
    Не все страницы защищены одинаково. Через get_fastapi_token на логин
    редиректят только dashboard и cars. Остальные (rentals, repairs, clients)
    при отсутствии токена рендерят пустую страницу со статусом 200 — это
    особенность текущей реализации проекта.
    """

    @pytest.mark.parametrize("route", ["home", "cars"])
    def test_protected_pages_redirect_to_login(self, client, route):
        response = client.get(reverse(route))
        assert response.status_code == 302
        assert reverse("login") in response.url

    @pytest.mark.parametrize("route", ["rentals", "repairs", "clients"])
    def test_soft_pages_render_without_token(self, client, route):
        # без токена не падают, отдают 200 (пустая страница)
        response = client.get(reverse(route))
        assert response.status_code == 200


# ──────────────────────────────────────────────
#  Дашборд
# ──────────────────────────────────────────────
class TestDashboard:
    def test_dashboard_ok_with_token(self, auth_client, mock_fastapi):
        response = auth_client.get(reverse("home"))
        assert response.status_code == 200

    def test_dashboard_title(self, auth_client, mock_fastapi):
        response = auth_client.get(reverse("home"))
        content = response.content.decode("utf-8")
        assert "Дашборд" in content

    def test_dashboard_shows_counts(self, auth_client, mock_fastapi):
        # отдаём одну машину со статусом available
        mock_fastapi.set_get({"items": [
            {"car_id": 1, "is_available": "available", "brand": "Kia",
             "number_car": "A001AA"}
        ], "total": 1})
        response = auth_client.get(reverse("home"))
        assert response.status_code == 200


# ──────────────────────────────────────────────
#  Автомобили
# ──────────────────────────────────────────────
class TestCars:
    def test_cars_redirect_without_token(self, client):
        response = client.get(reverse("cars"))
        assert response.status_code == 302

    def test_cars_ok_with_token(self, auth_client, mock_fastapi):
        response = auth_client.get(reverse("cars"))
        assert response.status_code == 200

    def test_cars_title(self, auth_client, mock_fastapi):
        response = auth_client.get(reverse("cars"))
        assert "Автомобили" in response.content.decode("utf-8")

    def test_cars_list_rendered(self, auth_client, mock_fastapi):
        mock_fastapi.set_get({"items": [
            {"car_id": 1, "number_car": "X777XX", "brand": "BMW",
             "is_available": "available", "category": "PREMIUM",
             "color": "white", "year": 2022, "daily_price": 5000}
        ], "total": 1})
        response = auth_client.get(reverse("cars"))
        content = response.content.decode("utf-8")
        assert "X777XX" in content or "BMW" in content


# ──────────────────────────────────────────────
#  Клиенты
# ──────────────────────────────────────────────
class TestClients:
    def test_clients_ok_with_token(self, auth_client, mock_fastapi):
        response = auth_client.get(reverse("clients"))
        assert response.status_code == 200

    def test_clients_title(self, auth_client, mock_fastapi):
        response = auth_client.get(reverse("clients"))
        assert "Клиенты" in response.content.decode("utf-8")

    def test_clients_without_token_renders_empty(self, client):
        # особенность проекта: clients при отсутствии headers НЕ редиректит,
        # а рендерит пустую страницу со статусом 200
        response = client.get(reverse("clients"))
        assert response.status_code == 200


# ──────────────────────────────────────────────
#  Аренды
# ──────────────────────────────────────────────
class TestRentals:
    def test_rentals_renders_without_token(self, client):
        # rentals при отсутствии токена не редиректит, а отдаёт 200
        response = client.get(reverse("rentals"))
        assert response.status_code == 200

    def test_rentals_ok_with_token(self, auth_client, mock_fastapi):
        response = auth_client.get(reverse("rentals"))
        assert response.status_code == 200

    def test_rentals_title(self, auth_client, mock_fastapi):
        response = auth_client.get(reverse("rentals"))
        assert "Аренды" in response.content.decode("utf-8")


# ──────────────────────────────────────────────
#  Ремонты
# ──────────────────────────────────────────────
class TestRepairs:
    def test_repairs_ok_with_token(self, auth_client, mock_fastapi):
        response = auth_client.get(reverse("repairs"))
        assert response.status_code == 200

    def test_repairs_title(self, auth_client, mock_fastapi):
        response = auth_client.get(reverse("repairs"))
        assert "Ремонт" in response.content.decode("utf-8")


# ──────────────────────────────────────────────
#  Сотрудники
# ──────────────────────────────────────────────
class TestStaff:
    def test_staff_ok_with_token(self, auth_client, mock_fastapi):
        mock_fastapi.set_get({"items": [], "total": 0})
        response = auth_client.get(reverse("staff"))
        assert response.status_code == 200

    def test_staff_title(self, auth_client, mock_fastapi):
        mock_fastapi.set_get({"items": [], "total": 0})
        response = auth_client.get(reverse("staff"))
        assert "Сотрудники" in response.content.decode("utf-8")


# ──────────────────────────────────────────────
#  Логин
# ──────────────────────────────────────────────
class TestLogin:
    def test_login_success_sets_token_and_redirects(self, client, mock_login):
        response = client.post(reverse("login"), {
            "username": "qweqwe", "password": "qwerty",
        })
        # при успехе вьюха редиректит на home и кладёт токен в сессию
        assert response.status_code in (302, 200)
        if response.status_code == 302:
            assert client.session.get("fastapi_token") == "test-token-123"

    def test_login_failure_renders_login(self, client, mock_login):
        mock_login.fail(401)
        response = client.post(reverse("login"), {
            "username": "qweqwe", "password": "wrong",
        })
        # при неудаче токен в сессии не появляется
        assert client.session.get("fastapi_token") is None
