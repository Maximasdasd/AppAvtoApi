from django.shortcuts import render, redirect
from core.fastapi_client import get_fastapi_token, auto_login_to_fastapi, get_headers
import requests
from django.contrib import messages
# для пагинации
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage, PageNotAnInteger
from django_service.settings import FASTAPI_BASE_URL
from core.views.utils import get_fastapi, get_role, get_sub, TokenExpired


def repairs(request):
    headers = get_headers(request)
    context = {'repairs': []}
    
    if not headers:
        messages.error(request, 'Ошибка авторизации')
        return render(request, 'repair/repairs.html', context)
    
    try:
        response = requests.get(
            f'{FASTAPI_BASE_URL}/repair/get_repair_all',  
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            repairs_data = response.json()
            context['repairs'] = repairs_data
            return render(request, 'repair/repairs.html', context)
            
        elif response.status_code == 401:
            return redirect('login')
        
        else:
            # Вместо редиректа на ту же страницу — показываем шаблон с ошибкой
            messages.error(request, f'Ошибка загрузки: код {response.status_code}')
            return render(request, 'repair/repairs.html', context)
            
    except requests.exceptions.ConnectionError:
        messages.error(request, 'Не удалось подключиться к серверу')
        return render(request, 'repair/repairs.html', context)
    except Exception as e:
        messages.error(request, f'Ошибка repairs: {str(e)}')
        return render(request, 'repair/repairs.html', context)

def repairs_create(request):
    headers = get_headers(request)
    
    if not headers:
        messages.error(request, 'Ошибка авторизации')
        return redirect('login')
    # start_time
    # car_id
    # price
    # ===== POST-запрос: обрабатываем отправку формы =====
    if request.method == 'POST':
        # Получаем данные из формы
        car_id = request.POST.get('car_id')
        start_time = request.POST.get('start_time')
        price = request.POST.get('price')

        # Валидация
        if not all([car_id, start_time, price]):
            messages.error(request, 'Заполните все поля')
            return redirect('repairs_create')
        
        # Готовим данные для отправки в FastAPI
        rental_data = {
            'car_id': int(car_id),
            'start_rep': start_time,
            'price_rep': price,
        }
        
        try:
            response = requests.post(
                f'{FASTAPI_BASE_URL}/repair/create_repair',
                json=rental_data,
                timeout=10,
                headers=headers
            )
            
            if response.status_code == 201:
                messages.success(request, 'Ремонт успешно создан')
                return redirect('repairs')
            elif response.status_code == 401:
                return redirect('login')
            else:
                error_msg = response.json().get('detail', 'Неизвестная ошибка')
                messages.error(request, f'Ошибка: {error_msg}')
                
        except requests.exceptions.ConnectionError:
            messages.error(request, 'Не удалось подключиться к серверу FastAPI')
        except Exception as e:
            messages.error(request, f'Ошибка repairs_create: {str(e)}')
        
        return redirect('repairs_create')
    
    # ===== GET-запрос: показываем форму =====
    try:
        response_cars = requests.get(
            f'{FASTAPI_BASE_URL}/car/get_cars_all',
            headers=headers,
            timeout=10
        )
        
        if response_cars.status_code == 401:
            return redirect('login')
        
        if response_cars.status_code != 200:
            messages.error(request, 'Ошибка загрузки списка автомобилей')
            return redirect('repairs_create')
        
        cars = response_cars.json()
        
        # Фильтруем только свободные автомобили
        cars_is_available = [car for car in cars.get('items', []) if car.get('is_available') == 'available']
        context = {
            'cars_is_available': cars_is_available,
        }
        return render(request, 'repair/repair_create.html', context)
        
    except requests.exceptions.ConnectionError:
        messages.error(request, 'Не удалось подключиться к серверу FastAPI')
        return redirect('repairs')
    except Exception as e:
        messages.error(request, f'Ошибка: {str(e)}')
        return redirect('repairs')

def repairs_detail(request, pk):

    role = get_role(request)
    headers = get_headers(request)
    context = {'repair': [],
               'role': role}
    
    if not headers:
        messages.error(request, 'Ошибка авторизации')
        return render(request, 'repair/repairs.html', context)
    
    try:
        response = requests.get(
            f'{FASTAPI_BASE_URL}/repair/get_repair_by_id',
            params={'repair_id': pk},
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            repair_data = response.json()
            context['repair'] = repair_data
            return render(request, 'repair/repair_detail.html', context)
            
        elif response.status_code == 401:
            return redirect('login')
        
        else:
            # Вместо редиректа на ту же страницу — показываем шаблон с ошибкой
            messages.error(request, f'Ошибка загрузки: код {response.status_code}')
            return render(request, 'repair/repairs.html', context)
            
    except requests.exceptions.ConnectionError:
        messages.error(request, 'Не удалось подключиться к серверу')
        return render(request, 'repair/repairs.html', context)
    except Exception as e:
        messages.error(request, f'Ошибка repairs_detail: {str(e)}')
    return render(request, 'repair/repairs.html', context)

def repairs_delete(request, pk):
    headers = get_headers(request)
    try:
        if headers:
            response = requests.delete(
                f'{FASTAPI_BASE_URL}/repair/delete_repair_by_id',  # ваш эндпоинт
                params={'repair_id': pk},
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                messages.success(request, f'Ремонт #{pk} успешно удален')
                return redirect('repairs')
            elif response.status_code == 401:
                return redirect('login')
            elif response.status_code == 404:
                messages.error(request, 'Аренда не найден')
                return redirect('repairs')
            else:
                messages.error(request, 'Ошибка при загрузке данных')
                return redirect('repairs')
    except requests.exceptions.ConnectionError:
        messages.error(request, 'Не удалось подключиться к серверу')
        return redirect('repairs')
    except Exception as e:
        messages.error(request, f'Ошибка repair_delete: {str(e)}')
        return redirect('repairs')
    return render(request, 'repair/repairs.html')



def repair_complete(request, pk):
    from datetime import datetime, timezone
    headers = get_headers(request)
    try:
        if headers:
            now_utc = datetime.now(timezone.utc)

            end_rep_formatted = now_utc.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            response = requests.patch(
                f'{FASTAPI_BASE_URL}/repair/complete_repair',  # ваш эндпоинт
                params={'repair_id': pk},
                json={'end_rep' : end_rep_formatted},
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                messages.success(request, f'Ремонт #{pk} успешно завершен')
                return redirect('repairs')
            elif response.status_code == 401:
                return redirect('login')
            elif response.status_code == 404:
                messages.error(request, 'Ремонт не найден')
                return redirect('repairs')
            else:
                messages.error(request, 'Ошибка при загрузке данных')
                return redirect('repairs')
    except requests.exceptions.ConnectionError:
        messages.error(request, 'Не удалось подключиться к серверу')
        return redirect('repairs')
    except Exception as e:
        messages.error(request, f'Ошибка repair_complete: {str(e)}')
        return redirect('repairs')
    return render(request, 'repair/repairs.html')
