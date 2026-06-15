from django.shortcuts import render, redirect
from core.fastapi_client import get_fastapi_token, auto_login_to_fastapi, get_headers
import requests
from django.contrib import messages
# для пагинации
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage, PageNotAnInteger
from django_service.settings import FASTAPI_BASE_URL
from core.views.utils import get_fastapi, get_role, get_sub, TokenExpired


def clients(request):
    headers = get_headers(request)
    
    if not headers:
        messages.error(request, 'Ошибка авторизации')
        return render(request, 'client/clients.html', {'clients': {'items': []}, 'clients_total': 0})
    
    # Получаем параметр поиска из GET-запроса
    search_query = request.GET.get('search', '').strip()
    
    try:
        response = requests.get(
            f'{FASTAPI_BASE_URL}/client/get_clients_all',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            client_data = response.json()
            clients_list = client_data.get('items', [])
            # Поиск по ФИО или телефону
            if search_query:
                search_lower = search_query.lower()
                clients_list = [
                    client for client in clients_list
                    if search_lower in client.get('full_name', '').lower()
                    or search_lower in client.get('phone', '').lower()
                ]
            
            context = {
                'clients': {'items': clients_list},
                'clients_total': len(clients_list),
                'search_query': search_query,  # передаём для отображения в поле поиска
            }
            return render(request, 'client/clients.html', context)
            
        elif response.status_code == 401:
            return redirect('login')
        else:
            error_detail = response.json().get('detail', 'Неизвестная ошибка')
            messages.error(request, f'Ошибка clients: {error_detail}')
            
    except requests.exceptions.ConnectionError:
        messages.error(request, 'Не удалось подключиться к серверу FastAPI')
    except Exception as e:
        messages.error(request, f'Ошибка: {str(e)}')
    
    return render(request, 'client/clients.html', {'clients': {'items': []}, 'clients_total': 0})


def client_create(request):
    headers=get_headers(request)
    if request.method != 'POST':
        return render(request, 'client/client_create.html')
    
    # Получаем данные из формы
    passport = request.POST.get('passport')
    address = request.POST.get('address')
    driver_license = request.POST.get('driver_license')
    full_name = request.POST.get('full_name')
    # Простая валидация чтобы все поля были заполнены
    if not all([passport, address, driver_license, full_name]):
        messages.error(request, 'Заполните все поля')
        return render(request, 'client/client_create.html')
    # Готовим данные для отправки в FastAPI
    client_data = {
        'full_name': full_name,
        'driver_license': driver_license,
        'passport': passport,
        'address': address
    }
    try:
        if headers:
            response = requests.post(
                f'{FASTAPI_BASE_URL}/client/create_client',  # твой FastAPI endpoint
                json=client_data,
                timeout=10,
                headers=headers
            )
        
        if response.status_code == 201:
            messages.success(request, 'Клиент успешно добавлен')
        elif response.status_code == 401:
            return redirect('login')
        else:
            messages.error(request, f'Ошибка: {response.json().get("detail", "Неизвестная ошибка")}')
    
    except requests.exceptions.ConnectionError:
        messages.error(request, 'Не удалось подключиться к серверу FastAPI')
    except Exception as e:
        messages.error(request, f'Ошибка client_create: {str(e)}')
    
    return redirect('client_create')

def client_detail(request, pk):
    headers = get_headers(request)
    
    # Получаем данные автомобиля из FastAPI
    try:
        if headers:
            response = requests.get(
                f'{FASTAPI_BASE_URL}/client/get_client/{pk}',  # ваш эндпоинт
                params={'id': pk},
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                client_data = response.json()
                # Получаем историю аренд для этого авто
                rentals_response = requests.get(
                    f'{FASTAPI_BASE_URL}/rental/get_rent_by_client_id',  # ваш эндпоинт
                    params={'client_id': pk},
                    headers=headers,
                    timeout=10
                )
                rentals = rentals_response.json() if rentals_response.status_code == 200 else []
                context = {
                    'client': client_data,
                    'rentals': rentals,
                }
                return render(request, 'client/client_detail.html', context)
            elif response.status_code == 404:
                messages.error(request, 'Клиент не найден')
                return redirect('clients')
            else:
                messages.error(request, 'Ошибка при загрузке данных')
                return redirect('clients')
                
    except requests.exceptions.ConnectionError:
        messages.error(request, 'Не удалось подключиться к серверу')
        return redirect('clients')
    except Exception as e:
        messages.error(request, f'Ошибка client_detail: {str(e)}')
        return redirect('clients')