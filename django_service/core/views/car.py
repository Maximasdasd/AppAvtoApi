from django.shortcuts import render, redirect
from core.fastapi_client import get_fastapi_token, auto_login_to_fastapi, get_headers
import requests
from django.contrib import messages
# для пагинации
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage, PageNotAnInteger
from django_service.settings import FASTAPI_BASE_URL
from core.views.utils import get_fastapi, get_role, get_sub, TokenExpired


def cars(request):
    token = get_fastapi_token(request)
    if not token:
        return redirect('login')

    # Получаем параметры из GET-запроса
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')

    context = {}
    try:
        data_cars = get_fastapi(request, "car/get_cars_all")
        
        # Извлекаем список автомобилей
        if isinstance(data_cars, dict):
            cars_list = data_cars.get('items', [])
        else:
            cars_list = data_cars if isinstance(data_cars, list) else []
        
        # Фильтрация по статусу
        if status_filter:
            status_map = {
                'free': 'available',
                'rented': 'rented',
                'repair': 'under_repair'
            }
            filter_status = status_map.get(status_filter)
            if filter_status:
                cars_list = [car for car in cars_list if car.get('is_available') == filter_status]
        
        # Поиск по гос. номеру или модели
        if search_query:
            search_lower = search_query.lower()
            cars_list = [
                car for car in cars_list
                if search_lower in car.get('number_car', '').lower()
                or search_lower in car.get('brand', '').lower()
                or search_lower in car.get('model', '').lower()
            ]
        
        context["cars"] = cars_list

    except TokenExpired:
        return redirect('login')
    except Exception as e:
        print(f"Ошибка при получении данных cars: {e}")
        context["cars"] = []

    return render(request, 'car/cars.html', context)


def cars_create(request):
    headers=get_headers(request)
    if request.method != 'POST':
        return render(request, 'car/car_create.html')
    
    # Получаем данные из формы
    number_car = request.POST.get('number_car')
    brand = request.POST.get('brand')
    category = request.POST.get('category')
    color = request.POST.get('color')
    year_release = request.POST.get('year_release')
    daily_price = request.POST.get('daily_price')

    # Простая валидация чтобы все поля были заполнены
    if not all([number_car, brand, category, color, year_release, daily_price]):
        messages.error(request, 'Заполните все поля')
        return render(request, 'car/car_create.html')
    # Готовим данные для отправки в FastAPI
    car_data = {
        'number_car': number_car,
        'brand': brand,
        'category': category,
        'color': color,
        'year': int(year_release),
        'daily_price': float(daily_price),
    }
    # Отправляем запрос в FastAPI
    try:
        if headers:
            response = requests.post(
                f'{FASTAPI_BASE_URL}/car/create_car',  # твой FastAPI endpoint
                json=car_data,
                timeout=10,
                headers=headers
            )
        
        if response.status_code == 201:
            messages.success(request, 'Автомобиль успешно добавлен')
        elif response.status_code == 401:
            return redirect('login')
        else:
            messages.error(request, f'Ошибка: {response.json().get("detail", "Неизвестная ошибка")}')
    
    except requests.exceptions.ConnectionError:
        messages.error(request, 'Не удалось подключиться к серверу FastAPI')
    except Exception as e:
        messages.error(request, f'Ошибка cars_create: {str(e)}')
    
    return redirect('cars')

def cars_detail(request, pk):
    headers = get_headers(request)
    
    # Получаем данные автомобиля из FastAPI
    try:
        if headers:
            response = requests.get(
                f'{FASTAPI_BASE_URL}/car/get_car/{pk}',  # ваш эндпоинт
                params={'car_id': pk},
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                car_data = response.json()
                
                # Получаем историю аренд для этого авто
                rentals_response = requests.get(
                    f'{FASTAPI_BASE_URL}/rental/get_rent_by_car_id',  # ваш эндпоинт
                    params={'car_id': pk},
                    headers=headers,
                    timeout=10
                )
                rentals = rentals_response.json() if rentals_response.status_code == 200 else []
                context = {
                    'car': car_data,
                    'car_rentals': rentals,
                }
                return render(request, 'car/car_detail.html', context)
            elif response.status_code == 404:
                messages.error(request, 'Автомобиль не найден')
                return redirect('cars')
            else:
                messages.error(request, 'Ошибка при загрузке данных')
                return redirect('cars')
                
    except requests.exceptions.ConnectionError:
        messages.error(request, 'Не удалось подключиться к серверу')
        return redirect('cars')
    except Exception as e:
        messages.error(request, f'Ошибка cars_detail: {str(e)}')
        return redirect('cars')

def car_delete(request, pk):
    headers = get_headers(request)
    if request.method == 'POST':
        response = requests.delete(
            f'{FASTAPI_BASE_URL}/car/delete_car/{pk}',
            params={'car_id': pk},
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            messages.success(request, f'Автомобиль #{pk} успешно удалён')
        elif response.status_code == 401:
            return redirect('login')
        else:
            messages.error(request, f'Ошибка cars_delete: {response.json().get("detail", "Неизвестная ошибка")}')
    
    return redirect('cars')