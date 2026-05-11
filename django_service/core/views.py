from django.shortcuts import render, redirect
from core.fastapi_client import get_fastapi_token, auto_login_to_fastapi, get_headers
import requests
from django.contrib import messages
# для пагинации
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage, PageNotAnInteger

FASTAPI_BASE_URL = "http://127.0.0.1:8000"

    # Функция для получения данных из FastAPI
def get_fastapi(request, url):
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
                
    # client stats 
    try:
        data_client = get_fastapi(request, "client/get_clients_all")
        client_is_active = [i for i in data_client["items"] if i['is_active']]
        context["client_isactive"] = len(client_is_active)
        context['total_client'] = len(data_client['items'])
    except Exception as e:
        print(f"Исключение при запросе к FastAPI: {e}")
        context["total_client"] = 0
        context['client_isactive'] = 0

    # cars stats + list
    try:
        data_cars = get_fastapi(request, "car/get_cars_all")
        cars_is_available = [i for i in data_cars["items"] if i['is_available'] == 'available']
        context["cars_is_available"] = len(cars_is_available)
        context["total_cars"] = len(data_cars['items'])
        context["cars"] = data_cars['items']
    except Exception as e:
        print(f"Исключение при запросе к FastAPI: {e}")
        context["total_cars"] = 0
        context["cars"] = []
        context["cars_is_available"] = 0
    
    # rentals stats
    try:
        data_rent = get_fastapi(request, "car/get_cars_all")
        cars_is_rented = [i for i in data_rent["items"] if i['is_available'] == 'rented']
        context["cars_is_rented"] = len(cars_is_rented)
    except Exception as e:
        print(f"Исключение при запросе к FastAPI: {e}")
        context["total_rent"] = 0


    # repairs stats
    try:
        data_repair = get_fastapi(request, "car/get_cars_all")
        cars_is_repair = [i for i in data_repair["items"] if i['is_available'] == 'under_repair']
        context["cars_is_repair"] = len(cars_is_repair)
    except Exception as e:
        print(f"Исключение при запросе к FastAPI: {e}")
        context["total_rent"] = 0

    # rentals_all list
    try:
        data_rental = get_fastapi(request, "rental/get_rental_all")
        context['rentals'] = data_rental['items']
    except Exception as e:
        print(f"Исключение при запросе к FastAPI: {e}")
        context["rentals"] = []
    
    # repair list

    try:
        data_repair = get_fastapi(request, 'repair/get_repair_all')
        context['repairs'] = data_repair['items']
    except Exception as e:
        print(f"Исключение при запросе к FastAPI: {e}")
        context["repairs"] = []
    
    return render(request, 'dashboard.html', context)



def car_create(request):
    headers=get_headers(request)
    if request.method != 'POST':
        return redirect('home')
    
    # Получаем данные из формы
    number_car = request.POST.get('number_car')
    brand = request.POST.get('brand')
    category = request.POST.get('category')
    color = request.POST.get('color')
    year_release = request.POST.get('year_release')
    daily_price = request.POST.get('daily_price')

    # print(f"number_car:{number_car}, brand:{brand}, category:{category}, color:{color}, year_release:{year_release}, daily_price:{daily_price}")
    # Простая валидация чтобы все поля были заполнены
    if not all([number_car, brand, category, color, year_release, daily_price]):
        messages.error(request, 'Заполните все поля')
        return redirect('home')
    # Готовим данные для отправки в FastAPI
    car_data = {
        'number_car': number_car,
        'brand': brand,
        'category': category,
        'color': color,
        'year': int(year_release),
        'daily_price': float(daily_price),
    }
    print(f"Данные: {car_data}")
    # Отправляем запрос в FastAPI
    try:
        if headers:
            response = requests.post(
                f'{FASTAPI_BASE_URL}/car/create_car',  # твой FastAPI endpoint
                json=car_data,
                timeout=10,
                headers=headers
            )
        
        if response.status_code == 200:
            print
            messages.success(request, 'Автомобиль успешно добавлен')
        else:
            messages.error(request, f'Ошибка: {response.json().get("detail", "Неизвестная ошибка")}')
    
    except requests.exceptions.ConnectionError:
        messages.error(request, 'Не удалось подключиться к серверу FastAPI')
    except Exception as e:
        messages.error(request, f'Ошибка: {str(e)}')
    
    return redirect('home')


def rent_complete(request):
    headers = get_headers(request)

    if headers:
        pass