from django.shortcuts import render, redirect
from core.fastapi_client import get_fastapi_token, auto_login_to_fastapi, get_headers
import requests
from django.contrib import messages
# для пагинации
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage, PageNotAnInteger
from django_service.settings import FASTAPI_BASE_URL
from core.views.utils import get_fastapi, get_role, get_sub, TokenExpired



def rentals(request):
    headers = get_headers(request)
    # Получаем данные автомобиля из FastAPI
    context ={}
    if headers:
        response = requests.get(
                f'{FASTAPI_BASE_URL}/rental/get_rental_all/',
                headers=headers,
                timeout=10)
        response_rent_ACTIVE = requests.get(
                f'{FASTAPI_BASE_URL}/rental/get_rent_by_status',
                  params={'status_rent':'ACTIVE'},
                headers=headers,
                timeout=10)
        response_rent_COMPLETED = requests.get(
                f'{FASTAPI_BASE_URL}/rental/get_rent_by_status',
                  params={'status_rent': 'COMPLETED'},
                headers=headers,
                timeout=10)
        
        response_rent_CANCELLED = requests.get(
                f'{FASTAPI_BASE_URL}/rental/get_rent_by_status',
                  params={'status_rent':'CANCELLED'} ,
                headers=headers,
                timeout=10)
        active_count=response_rent_ACTIVE.json()
        if active_count == {'error': 'Не найдено'}:
            active_count = {"items": []}
        completed_count=response_rent_COMPLETED.json()
        if completed_count == {'error': 'Не найдено'}:
            completed_count = {"items": []}
        cancelled_count=response_rent_CANCELLED.json()
        if cancelled_count == {'error': 'Не найдено'}:
            cancelled_count = {"items": []}
        if response.status_code == 200:
            rentals = response.json()
            context = {'rentals' : rentals,
                       'active_count': len(active_count['items']),
                        'completed_count': len(completed_count['items']),
                        'cancelled_count': len(cancelled_count['items']),
                        }
        elif response.status_code == 401:
                    return redirect('login')
        else:
            messages.error(request, f'Ошибка rentals: {response.json().get("detail", "Неизвестная ошибка")}')

    return render(request, 'rental/rentals.html', context)



def rentals_create(request):
    headers = get_headers(request)
    
    if not headers:
        messages.error(request, 'Ошибка авторизации')
        return redirect('login')
    
    # ===== POST-запрос: обрабатываем отправку формы =====
    if request.method == 'POST':
        # Получаем данные из формы
        car_id = request.POST.get('car_id')
        client_id = request.POST.get('client_id')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        
        # Валидация
        if not all([car_id, client_id, start_time, end_time]):
            messages.error(request, 'Заполните все поля')
            return redirect('rentals_create')
        
        # Готовим данные для отправки в FastAPI
        rental_data = {
            'car_id': int(car_id),
            'client_id': int(client_id),  # ← исправлено!
            'start_time': start_time,
            'end_time': end_time,
        }
        
        try:
            response = requests.post(
                f'{FASTAPI_BASE_URL}/rental/create_rental',
                json=rental_data,
                timeout=10,
                headers=headers
            )
            
            if response.status_code == 201:
                messages.success(request, 'Аренда успешно создана')
                return redirect('rentals')  # ← редирект на список аренд
            elif response.status_code == 401:
                return redirect('login')
            else:
                error_msg = response.json().get('detail', 'Неизвестная ошибка')
                messages.error(request, f'Ошибка: {error_msg}')
                
        except requests.exceptions.ConnectionError:
            messages.error(request, 'Не удалось подключиться к серверу FastAPI')
        except Exception as e:
            messages.error(request, f'Ошибка rental_create: {str(e)}')
        
        return redirect('rentals_create')
    
    # ===== GET-запрос: показываем форму =====
    try:
        response_clients = requests.get(
            f'{FASTAPI_BASE_URL}/client/get_clients_all',
            headers=headers,
            timeout=10
        )
        response_cars = requests.get(
            f'{FASTAPI_BASE_URL}/car/get_cars_all',
            headers=headers,
            timeout=10
        )
        
        if response_clients.status_code == 401 or response_cars.status_code == 401:
            return redirect('login')
        
        if response_clients.status_code != 200:
            messages.error(request, 'Ошибка загрузки списка клиентов')
            return redirect('rentals')
        
        if response_cars.status_code != 200:
            messages.error(request, 'Ошибка загрузки списка автомобилей')
            return redirect('rentals')
        
        clients = response_clients.json()
        cars = response_cars.json()
        
        # Фильтруем только свободные автомобили
        cars_is_available = [car for car in cars.get('items', []) if car.get('is_available') == 'available']
        
        context = {
            'clients': clients,
            'available_cars': cars_is_available,
        }
        return render(request, 'rental/rental_create.html', context)
        
    except requests.exceptions.ConnectionError:
        messages.error(request, 'Не удалось подключиться к серверу FastAPI')
        return redirect('rentals')
    except Exception as e:
        messages.error(request, f'Ошибка: {str(e)}')
        return redirect('rentals')

def rentals_detail(request, pk):
    headers = get_headers(request)
    try:
        if headers:
            response = requests.get(
                f'{FASTAPI_BASE_URL}/rental/get_rent_by_id',  # ваш эндпоинт
                params={'rent_id': pk},
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                rental = response.json()
                context = {
                    'rental': rental,
                }
                return render(request, 'rental/rental_detail.html', context)
            elif response.status_code == 401:
                return redirect('login')
            elif response.status_code == 404:
                messages.error(request, 'Аренда не найден')
                return redirect('rentals')
            else:
                messages.error(request, 'Ошибка при загрузке данных')
                return redirect('rentals')
                
    except requests.exceptions.ConnectionError:
        messages.error(request, 'Не удалось подключиться к серверу')
        return redirect('rentals')
    except Exception as e:
        messages.error(request, f'Ошибка rentals_detail: {str(e)}')
        return redirect('rentals')
    return render(request, 'rental/rental_detail.html')

def rental_complete(request, pk):
    headers = get_headers(request)
    try:
        if headers:
            response = requests.patch(
                f'{FASTAPI_BASE_URL}/rental/rent_complete',  # ваш эндпоинт
                params={'rent_id': pk},
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                messages.success(request, f'Аренда #{pk} успешно завершена')
                return redirect('rentals')
            elif response.status_code == 401:
                return redirect('login')
            elif response.status_code == 404:
                messages.error(request, 'Аренда не найден')
                return redirect('rentals')
            else:
                messages.error(request, 'Ошибка при загрузке данных')
                return redirect('rentals')
    except requests.exceptions.ConnectionError:
        messages.error(request, 'Не удалось подключиться к серверу')
        return redirect('rentals')
    except Exception as e:
        messages.error(request, f'Ошибка rental_complete: {str(e)}')
        return redirect('rentals')
    return redirect('rentals')

def rental_cancel(request, pk):
    headers = get_headers(request)
    try:
        if headers:
            response = requests.patch(
                f'{FASTAPI_BASE_URL}/rental/rent_cancelled',  # ваш эндпоинт
                params={'rent_id': pk},
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                messages.success(request, f'Аренда #{pk} успешно отменена')
                return redirect('rentals')
            elif response.status_code == 401:
                return redirect('login')
            elif response.status_code == 404:
                messages.error(request, 'Аренда не найден')
                return redirect('rentals')
            else:
                messages.error(request, 'Ошибка при загрузке данных')
                return redirect('rentals')
    except requests.exceptions.ConnectionError:
        messages.error(request, 'Не удалось подключиться к серверу')
        return redirect('rentals')
    except Exception as e:
        messages.error(request, f'Ошибка rental_cancel: {str(e)}')
        return redirect('rentals')
    return redirect('rentals')