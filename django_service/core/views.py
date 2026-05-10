from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.conf import settings
from django.contrib import messages
import requests

FASTAPI_BASE_URL = "http://127.0.0.1:8000"

def hello(request):
    return HttpResponse("Тестовый URL работает!")

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

def dashboard(request):
    """
    Дашборд с автоматическим получением токена, если его нет.
    """
    # Если токена нет — пытаемся автоматически авторизоваться
    token = get_fastapi_token(request)
    if not token:
        success = auto_login_to_fastapi(request)
        if not success:
            context = {
                'total_cars': 0,
                'total_client': 0,
                'total_rent': 0,
                'total_repair': 0,
                'rentals': [],
                'cars': [],
                'repairs': [],
                'error': 'Не удалось авторизоваться в FastAPI. Проверьте учетные данные.'
            }
            return render(request, 'dashboard.html', context)

    headers = get_headers(request)
    context = {
        'total_rent': 0,
        'total_repair': 0
    }

    try:
        resp_client = requests.get(
            f"{FASTAPI_BASE_URL}/client/get_clients_all",
            headers=headers,
            timeout=5
        )
        if resp_client.ok:
                client_data = resp_client.json()
                is_active= [i for i in client_data['items'] if i['is_active']]
                context["client_isactive"] = len(is_active)
                context["total_client"] = len(client_data['items'])
                context["client"] = client_data['items']
        elif resp_client.status_code == 401:
            # Токен протух — пробуем перелогиниться
            success = auto_login_to_fastapi(request)
            if success:
                # Повторяем запрос с новым токеном
                headers = get_headers(request)
                resp_client = requests.get(
                    f"{FASTAPI_BASE_URL}/client/get_clients_all",
                    headers=headers,
                    timeout=5
                )
                if resp_client.ok:
                    client_data = resp_client.json()
                    context["total_client"] = len(client_data)
                    context["client"] = client_data
        else:
            print(f"Ошибка FastAPI: {resp_client.status_code}")

    except Exception as e:
        print(f"Исключение при запросе к FastAPI: {e}")
        context["total_client"] = 0

    
    try:
        resp_cars = requests.get(
            f"{FASTAPI_BASE_URL}/car/get_cars_all",
            headers=headers,
            timeout=5
        )
        
        if resp_cars.ok:
            cars_data = resp_cars.json()
            context["total_cars"] = len(cars_data['items'])
            context["cars"] = cars_data['items']
        elif resp_cars.status_code == 401:
            # Токен протух — пробуем перелогиниться
            success = auto_login_to_fastapi(request)
            if success:
                # Повторяем запрос с новым токеном
                headers = get_headers(request)
                resp_cars = requests.get(
                    f"{FASTAPI_BASE_URL}/car/get_cars_all",
                    headers=headers,
                    timeout=5
                )
                if resp_cars.ok:
                    cars_data = resp_cars.json()
                    context["total_cars"] = len(cars_data)
                    context["cars"] = cars_data
        else:
            print(f"Ошибка FastAPI: {resp_cars.status_code}")
            
    except Exception as e:
        print(f"Исключение при запросе к FastAPI: {e}")
        context["total_cars"] = 0

    return render(request, 'dashboard.html', context)

