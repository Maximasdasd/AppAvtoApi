"""
conftest.py — фикстуры для тестов Django-сервиса (AutoFleet / автопрокат).

ВАЖНО про архитектуру этого проекта:
Django здесь НЕ использует собственную модель пользователя (django User) для
бизнес-входа. Аутентификация устроена так:
  * пользователь логинится через /login_staff/ -> Django шлёт логин/пароль в FastAPI;
  * FastAPI возвращает JWT, который Django кладёт в сессию: request.session['fastapi_token'];
  * все страницы тянут данные из FastAPI через requests.* с этим токеном.

Поэтому НЕ используются фикстуры вида User.objects.create_user / client.login().
Вместо этого:
  * фикстура `auth_client` кладёт токен прямо в сессию;
  * фикстура `mock_fastapi` подменяет requests.get/post/patch/delete в core.views,
    чтобы тесты не ходили в реальный FastAPI.
"""
import pytest
from django.test import Client


# --- ALLOWED_HOSTS -------------------------------------------------------
# В settings.py ALLOWED_HOSTS = [], из-за чего Django test client (хост
# 'testserver') получает 400. Добавляем хост только на время тестов.
@pytest.fixture(autouse=True)
def _allow_testserver(settings):
    settings.ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]


# --- Клиенты -------------------------------------------------------------
@pytest.fixture
def client():
    """Анонимный Django test client (без токена FastAPI в сессии)."""
    return Client()


@pytest.fixture
def auth_client(client):
    """
    Клиент с «залогиненным» пользователем: в сессии лежит токен FastAPI.
    Этого достаточно, чтобы пройти проверки get_fastapi_token / get_headers.
    """
    session = client.session
    session["fastapi_token"] = "test-token-123"
    session.save()
    return client


# --- Мок ответов FastAPI -------------------------------------------------
class FakeResponse:
    """Имитация requests.Response."""
    def __init__(self, json_data=None, status_code=200):
        self._json = json_data if json_data is not None else {}
        self.status_code = status_code
        self.ok = status_code < 400
        self.text = str(self._json)

    def json(self):
        return self._json


def _empty_page():
    return {"items": [], "total": 0, "page": 1, "size": 50, "pages": 1}


@pytest.fixture
def fake_response():
    """Доступ к классу FakeResponse и хелперу пустой страницы из тестов."""
    return {"Response": FakeResponse, "empty_page": _empty_page}


@pytest.fixture
def mock_fastapi(monkeypatch):
    """
    Подменяет все HTTP-вызовы к FastAPI в core.views на безопасные заглушки.
    По умолчанию любой GET/POST/PATCH/DELETE возвращает 200 и пустую страницу.
    Тест может донастроить поведение через возвращаемый объект `m`.
    """
    import requests

    state = {
        "get": FakeResponse(_empty_page(), 200),
        "post": FakeResponse({"detail": "ok"}, 201),
        "patch": FakeResponse({"detail": "ok"}, 200),
        "delete": FakeResponse({"detail": "ok"}, 200),
    }

    monkeypatch.setattr(requests, "get", lambda *a, **k: state["get"])
    monkeypatch.setattr(requests, "post", lambda *a, **k: state["post"])
    monkeypatch.setattr(requests, "patch", lambda *a, **k: state["patch"])
    monkeypatch.setattr(requests, "delete", lambda *a, **k: state["delete"])

    class Controller:
        Response = FakeResponse
        empty_page = staticmethod(_empty_page)

        def set_get(self, json_data, status=200):
            state["get"] = FakeResponse(json_data, status)

        def set_post(self, json_data, status=201):
            state["post"] = FakeResponse(json_data, status)

        def set_patch(self, json_data, status=200):
            state["patch"] = FakeResponse(json_data, status)

        def set_delete(self, json_data, status=200):
            state["delete"] = FakeResponse(json_data, status)

    return Controller()


@pytest.fixture
def mock_login(monkeypatch):
    """
    Мок входа: подменяет requests.post в core.fastapi_client, чтобы
    /login_staff/ не ходил в реальный FastAPI.
    По умолчанию логин успешен и возвращает access_token.
    """
    import core.fastapi_client as fc

    state = {"resp": FakeResponse({"access_token": "test-token-123",
                                   "refresh_token": "r",
                                   "token_type": "bearer"}, 200)}

    monkeypatch.setattr(fc.requests, "post", lambda *a, **k: state["resp"])

    class LoginController:
        def fail(self, status=401):
            state["resp"] = FakeResponse({"detail": "bad"}, status)

    return LoginController()
