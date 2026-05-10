from django.http import HttpResponse
import requests

FASTAPI_BASE_URL = "http://127.0.0.1:8000"

def get_fastapi_token(request):
    """
    Получить токен из сессии Django.
    Если токена нет — значит пользователь не авторизован в FastAPI.
    """
    token = request.session.get("fastapi_token")
    if not token:
        return None
    return token


def get_headers(request):
    """
    Заголовки для запросов к FastAPI.
    """
    token = get_fastapi_token(request)
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def auto_login_to_fastapi(request):
    login_url = f"{FASTAPI_BASE_URL}/staff/login_staff"
    
    # Отправляем как form-data (как HTML-форма)
    resp = requests.post(
        login_url,
        data={"username": "qweqwe", "password": "qwerty"},
        timeout=5,
    )
    
    print(f"Логин ответ: {resp.status_code}")
    print(f"Логин тело: {resp.text[:300]}")
    
    if resp.ok:
        token_data = resp.json()
        print(f"Ключи в ответе: {list(token_data.keys())}")
        token = (
            token_data.get("access_token") or 
            token_data.get("token") or 
            token_data.get("accessToken")
        )
        if token:
            request.session["fastapi_token"] = token
            return True
    return False