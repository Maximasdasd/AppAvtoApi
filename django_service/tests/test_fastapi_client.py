"""
Тесты модуля core/fastapi_client.py — клиента к FastAPI.

Реальные функции этого модуля:
  * get_fastapi_token(request)   — достаёт токен из сессии (или None);
  * get_headers(request)         — формирует заголовок Authorization (или {});
  * auto_login_to_fastapi(request) — логинит в FastAPI и кладёт токен в сессию.
"""
import pytest
from unittest.mock import patch
from core.fastapi_client import get_fastapi_token, get_headers


class FakeSessionRequest:
    """Минимальный объект request с атрибутом session (dict)."""
    def __init__(self, session=None):
        self.session = session if session is not None else {}


#  get_fastapi_token
class TestGetToken:
    def test_returns_token_when_present(self):
        """Проверяет, что функция возвращает JWT-токен, если он есть в сессии."""
        req = FakeSessionRequest({"fastapi_token": "abc123"})
        assert get_fastapi_token(req) == "abc123"

    def test_returns_none_when_absent(self):
        """Проверяет, что функция возвращает None, если JWT-токен отсутствует в сессии."""
        req = FakeSessionRequest({})
        assert get_fastapi_token(req) is None


#  get_headers
class TestGetHeaders:
    def test_headers_with_token(self):
        """Проверяет, что при наличии токена формируется заголовок Authorization с Bearer-схемой."""
        req = FakeSessionRequest({"fastapi_token": "abc123"})
        assert get_headers(req) == {"Authorization": "Bearer abc123"}

    def test_headers_without_token(self):
        """Проверяет, что при отсутствии токена возвращается пустой словарь заголовков."""
        req = FakeSessionRequest({})
        assert get_headers(req) == {}


#  auto_login_to_fastapi
class TestAutoLogin:
    @patch("core.fastapi_client.requests.post")
    def test_login_success_saves_token(self, mock_post):
        """При 200 и наличии access_token токен сохраняется в сессию."""
        class Resp:
            status_code = 200
            ok = True
            text = '{"access_token":"tok"}'
            def json(self):
                return {"access_token": "tok", "token_type": "bearer"}
        mock_post.return_value = Resp()

        from core.fastapi_client import auto_login_to_fastapi

        class Req:
            method = "POST"
            session = {}
            POST = {"username": "qweqwe", "password": "qwerty"}

        req = Req()
        auto_login_to_fastapi(req)
        assert req.session.get("fastapi_token") == "tok"

    @patch("core.fastapi_client.requests.post")
    def test_login_sends_form_data(self, mock_post):
        """Логин отправляется как form-data (data=...), а не json."""
        class Resp:
            status_code = 200
            ok = True
            text = "{}"
            def json(self):
                return {"access_token": "tok"}
        mock_post.return_value = Resp()

        from core.fastapi_client import auto_login_to_fastapi

        class Req:
            method = "POST"
            session = {}
            POST = {"username": "u", "password": "p"}

        auto_login_to_fastapi(Req())
        _, kwargs = mock_post.call_args
        assert "data" in kwargs
        assert kwargs["data"]["username"] == "u"
