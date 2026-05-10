from django.shortcuts import render, redirect
from core.fastapi_client import get_fastapi_token, auto_login_to_fastapi, get_headers
import requests

# для пагинации
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage, PageNotAnInteger

FASTAPI_BASE_URL = "http://127.0.0.1:8000"

def account(request):
    pass



# dashboard view home
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

    
    context = {}

    # Функция для получения данных из FastAPI
    def get_fastapi(url):
        headers = get_headers(request)
        if headers:
            try:
                resp = requests.get(
                f"{FASTAPI_BASE_URL}/{url}",
                headers=headers,
                timeout=5
            )
                if resp.ok:
                    data = resp.json()
                    return data
                elif resp.status_code == 401:
                    # Токен протух — пробуем перелогиниться
                    success = auto_login_to_fastapi(request)
                if success:
                    # Повторяем запрос с новым токеном
                    headers = get_headers(request)
                    resp = requests.get(
                        f"{FASTAPI_BASE_URL}/{url}",
                        headers=headers,
                        timeout=5
                    )
                    if resp.ok:
                        data = resp.json()
                        return data
                else:
                    print(f"Ошибка FastAPI: {resp.status_code}")
                    return None
            except Exception as e:
                print(f"Исключение при запросе к FastAPI: {e}")
                return None
                

    # client
    try:
        data_client = get_fastapi("client/get_clients_all")
        client_is_active = [i for i in data_client["items"] if i['is_active']]
        context["client_isactive"] = len(client_is_active)
        context['total_client'] = len(data_client['items'])
    except Exception as e:
        print(f"Исключение при запросе к FastAPI: {e}")
        context["total_client"] = 0
        context['client_isactive'] = 0

    # cars
    try:
        data_cars = get_fastapi("car/get_cars_all")
        cars_is_available = [i for i in data_cars["items"] if i['is_available'] == 'available']
        context["cars_is_available"] = len(cars_is_available)
        context["total_cars"] = len(data_cars['items'])
        context["cars"] = data_cars['items']
    except Exception as e:
        print(f"Исключение при запросе к FastAPI: {e}")
        context["total_cars"] = 0
        context["cars"] = []
        context["cars_is_available"] = 0
    
    # rentals
    try:
        data_rent = get_fastapi("car/get_cars_all")
        cars_is_rented = [i for i in data_rent["items"] if i['is_available'] == 'rented']
        context["cars_is_rented"] = len(cars_is_rented)
    except Exception as e:
        print(f"Исключение при запросе к FastAPI: {e}")
        context["total_rent"] = 0


    # repairs
    try:
        data_repair = get_fastapi("car/get_cars_all")
        cars_is_repair = [i for i in data_repair["items"] if i['is_available'] == 'under_repair']
        context["cars_is_repair"] = len(cars_is_repair)
    except Exception as e:
        print(f"Исключение при запросе к FastAPI: {e}")
        context["total_rent"] = 0

    # rentals_all
    try:
        data_rental = get_fastapi("rental/get_rental_all")
        context['rentals'] = data_rental['items']
    except Exception as e:
        print(f"Исключение при запросе к FastAPI: {e}")
        context["rentals"] = []
    
    
    return render(request, 'dashboard.html', context)