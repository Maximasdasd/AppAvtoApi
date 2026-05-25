from django.shortcuts import render, redirect
from core.fastapi_client import get_fastapi_token, auto_login_to_fastapi, get_headers
import requests
from django.contrib import messages
# для пагинации
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage, PageNotAnInteger

FASTAPI_BASE_URL = "http://127.0.0.1:8000"


class TokenExpired(Exception):
    pass
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
                    request.session.flush()
                    raise TokenExpired
                else:
                    print(f"Ошибка FastAPI: {resp.status_code}")
                    return None
        except Exception as e:
            if isinstance(e, TokenExpired):
                raise   # пробрасываем дальше
            print(f"Исключение: {e}")
            return None

def get_role(request):
    try:
        headers = get_headers(request)
        response = requests.get(
                f'{FASTAPI_BASE_URL}/staff/info_me',
                headers=headers,
                timeout=10
            )
        if response.status_code == 200:
            return response.json()['roles'][0]
        else:
            redirect('login')
    except Exception as e:
        print('error get_payload')

def get_sub(request):
    try:
        headers = get_headers(request)
        response = requests.get(
                f'{FASTAPI_BASE_URL}/staff/info_me',
                headers=headers,
                timeout=10
            )
        if response.status_code == 200:
            return response.json()['sub']
        else:
            redirect('login')
    except Exception as e:
        print('error get_payload')



# dashboard view home
def dashboard(request):
    token = get_fastapi_token(request)
    if not token:
        return redirect('login')

    context = {}
    try:
        # client stats
        data_client = get_fastapi(request, "client/get_clients_all")
        client_is_active = [i for i in data_client["items"] if i['is_active']]
        context["client_isactive"] = len(client_is_active)
        context['total_client'] = len(data_client['items'])
        context['clients'] = data_client['items']

        # cars stats + list
        data_cars = get_fastapi(request, "car/get_cars_all")
        cars_is_available = [i for i in data_cars["items"] if i['is_available'] == 'available']
        context["cars_is_available"] = len(cars_is_available)
        context["available_cars_all"] = cars_is_available
        context["total_cars"] = len(data_cars['items'])
        context["cars"] = data_cars['items']

        # rentals stats
        data_rent = get_fastapi(request, "car/get_cars_all")
        cars_is_rented = [i for i in data_rent["items"] if i['is_available'] == 'rented']
        context["cars_is_rented"] = len(cars_is_rented)

        # repairs stats
        data_repair = get_fastapi(request, "car/get_cars_all")
        cars_is_repair = [i for i in data_repair["items"] if i['is_available'] == 'under_repair']
        context["cars_is_repair"] = len(cars_is_repair)

        # rentals_all list
        data_rental = get_fastapi(request, "rental/get_rental_all")
        context['rentals'] = data_rental['items']

        # repair list
        data_repair_list = get_fastapi(request, 'repair/get_repair_all')
        context['repairs'] = data_repair_list['items']

    except TokenExpired:
        return redirect('login')
    except Exception as e:
        print(f"Ошибка при получении данных: {e}")
        context.setdefault('clients', [])
        context.setdefault('cars', [])
        context.setdefault('rentals', [])
        context.setdefault('repairs', [])
        context.setdefault('total_client', 0)
        context.setdefault('total_cars', 0)
        context.setdefault('cars_is_rented', 0)
        context.setdefault('cars_is_repair', 0)


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
        messages.error(request, f'Ошибка: {str(e)}')
    
    return redirect('home')


def rent_create(request):
    headers=get_headers(request)

    if request.method != 'POST':
        return redirect('home')

    client_id = request.POST.get('client_id')
    car_id = request.POST.get('car_id')
    start_time = request.POST.get('start_time')
    end_time = request.POST.get('end_time')
    if not all([client_id, car_id, start_time, end_time]):
        messages.error(request, 'Заполните все поля')
        return redirect('home')

    rent_data = {
        'client_id': client_id,
        'car_id': car_id,
        'start_time': start_time,
        'end_time': end_time,
    }
        
    if headers:
        response = requests.post(
                f'{FASTAPI_BASE_URL}/rental/create_rental',  # твой FastAPI endpoint
                json=rent_data,
                timeout=10,
                headers=headers
            )
            
        if response.status_code == 201:
            messages.success(request, 'Автомобиль успешно добавлен')
        elif response.status_code == 401:
            return redirect('login')
        else:
            messages.error(request, f'Ошибка: {response.json().get("detail", "Неизвестная ошибка")}')
    return redirect('home')


def repair_create(request):
    headers = get_headers(request)
    if request.method == 'POST':
        car_id = request.POST.get('car_id')
        start_rep = request.POST.get('start_rep')
        price_rep = request.POST.get('price_rep')

        from datetime import datetime
        dt = datetime.strptime(start_rep, "%Y-%m-%dT%H:%M")
        start_rep_iso = dt.isoformat() + "Z" 
        
        repair_data = {
            "car_id": int(car_id),
            "start_rep": start_rep_iso,
            "price_rep": float(price_rep),
        }
        
        # Отправка в FastAPI
        if headers:
            response = requests.post(
                f"{FASTAPI_BASE_URL}/repair/create_repair",
                json=repair_data,
                headers=headers,
                timeout=10
            )
            
            if response.ok:
                messages.success(request, "Автомобиль отправлен в ремонт")
                return redirect('home')
            elif response.status_code == 401:
                return redirect('login')
            else:
                messages.error(request, f"Ошибка: {response.json().get('detail', 'Неизвестная ошибка')}")
        
    return redirect('home')


def complete_repair(request, repair_id):
    headers = get_headers(request)

    if request.method != 'POST':
        return redirect('home')

    end_rep = request.POST.get('end_rep')
    if not end_rep:
        messages.error(request, 'Укажите дату завершения ремонта')
        return redirect('home')

    # Преобразуем datetime-local в ISO-формат, который ожидает FastAPI
    try:
        from datetime import datetime
        dt = datetime.strptime(end_rep, "%Y-%m-%dT%H:%M")
        end_rep_iso = dt.isoformat() + "Z"  # Например: 2026-05-12T15:00:00Z
    except ValueError:
        messages.error(request, 'Неверный формат даты')
        return redirect('home')

    patch_data = {
        'end_rep': end_rep_iso
    }

    if headers:
        try:
            response = requests.patch(
                f'{FASTAPI_BASE_URL}/repair/complete_repair?repair_id={repair_id}',
                json=patch_data,
                timeout=10,
                headers=headers
            )
            if response.status_code == 200:
                messages.success(request, f'Ремонт #{repair_id} завершён')
            elif response.status_code == 401:
                return redirect('login')
            else:
                error_detail = response.json().get('detail', 'Неизвестная ошибка')
                messages.error(request, f'Ошибка: {error_detail}')
        except requests.exceptions.ConnectionError:
            messages.error(request, 'Не удалось подключиться к серверу FastAPI')
        except Exception as e:
            messages.error(request, f'Ошибка: {str(e)}')
    else:
        messages.error(request, 'Отсутствуют заголовки авторизации')

    return redirect('home')


def cancel_repair(request, repair_id):
    headers = get_headers(request)

    if request.method != 'POST':
        return redirect('home')

    if headers:
        try:
            response = requests.delete(
                f'{FASTAPI_BASE_URL}/repair/delete_repair_by_id?repair_id={repair_id}',
                json={},
                timeout=10,
                headers=headers
            )
            if response.status_code == 200:
                messages.success(request, f'Ремонт #{repair_id} отменён')
            elif response.status_code == 401:
                return redirect('login')
            else:
                error_detail = response.json().get('detail', 'Неизвестная ошибка')
                messages.error(request, f'Ошибка: {error_detail}')
        except requests.exceptions.ConnectionError:
            messages.error(request, 'Не удалось подключиться к серверу FastAPI')
        except Exception as e:
            messages.error(request, f'Ошибка: {str(e)}')
    else:
        messages.error(request, 'Отсутствуют заголовки авторизации')

    return redirect('home')


# авто
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

    return render(request, 'cars.html', context)


def cars_create(request):
    headers=get_headers(request)
    if request.method != 'POST':
        return render(request, 'car_create.html')
    
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
        return render(request, 'car_create.html')
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
                return render(request, 'car_detail.html', context)
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
            f'{FASTAPI_BASE_URL}/car/delete_car/{id}',
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

# клиенты

def clients(request):
    headers = get_headers(request)
    
    if not headers:
        messages.error(request, 'Ошибка авторизации')
        return render(request, 'clients.html', {'clients': {'items': []}, 'clients_total': 0})
    
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
            print(clients_list)
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
            return render(request, 'clients.html', context)
            
        elif response.status_code == 401:
            return redirect('login')
        else:
            error_detail = response.json().get('detail', 'Неизвестная ошибка')
            messages.error(request, f'Ошибка clients: {error_detail}')
            
    except requests.exceptions.ConnectionError:
        messages.error(request, 'Не удалось подключиться к серверу FastAPI')
    except Exception as e:
        messages.error(request, f'Ошибка: {str(e)}')
    
    return render(request, 'clients.html', {'clients': {'items': []}, 'clients_total': 0})


def client_create(request):
    headers=get_headers(request)
    if request.method != 'POST':
        return render(request, 'client_create.html')
    
    # Получаем данные из формы
    passport = request.POST.get('passport')
    address = request.POST.get('address')
    driver_license = request.POST.get('driver_license')
    full_name = request.POST.get('full_name')
    # Простая валидация чтобы все поля были заполнены
    if not all([passport, address, driver_license, full_name]):
        messages.error(request, 'Заполните все поля')
        return render(request, 'client_create.html')
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
                return render(request, 'client_detail.html', context)
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


# аренда
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

    return render(request, 'rentals.html', context)

def btn_rentals_create(request):
    pass

    # get
    # available_cars
    # clients
    # post
    # end_time
    # start_time
    # car_id    
    # client_id

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
            print([car_id, client_id, start_time, end_time])
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
        return render(request, 'rental_create.html', context)
        
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
                return render(request, 'rental_detail.html', context)
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
    return render(request, 'rental_detail.html')

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
                return render(request, 'rental_detail.html', {'pk': pk})
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
    return render(request, 'rental_detail.html', {'pk': pk})

def rental_cancel(request, pk):
    headers = get_headers(request)
    try:
        if headers:
            response = requests.post(
                f'{FASTAPI_BASE_URL}/rental/rent_cancelled',  # ваш эндпоинт
                params={'rent_id': pk},
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                messages.success(request, f'Аренда #{pk} успешно отменена')
                return render(request, 'rental_detail.html')
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
    return render(request, 'rental_detail.html')


# ремонт
def repairs(request):
    headers = get_headers(request)
    context = {'repairs': []}
    
    if not headers:
        messages.error(request, 'Ошибка авторизации')
        return render(request, 'repairs.html', context)
    
    try:
        response = requests.get(
            f'{FASTAPI_BASE_URL}/repair/get_repair_all',  
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            repairs_data = response.json()
            context['repairs'] = repairs_data
            return render(request, 'repairs.html', context)
            
        elif response.status_code == 401:
            return redirect('login')
        
        else:
            # Вместо редиректа на ту же страницу — показываем шаблон с ошибкой
            messages.error(request, f'Ошибка загрузки: код {response.status_code}')
            return render(request, 'repairs.html', context)
            
    except requests.exceptions.ConnectionError:
        messages.error(request, 'Не удалось подключиться к серверу')
        return render(request, 'repairs.html', context)
    except Exception as e:
        messages.error(request, f'Ошибка repairs: {str(e)}')
        return render(request, 'repairs.html', context)

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
                print(response.json())
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
        print( cars_is_available)
        context = {
            'cars_is_available': cars_is_available,
        }
        return render(request, 'repair_create.html', context)
        
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
        return render(request, 'repairs.html', context)
    
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
            return render(request, 'repair_detail.html', context)
            
        elif response.status_code == 401:
            return redirect('login')
        
        else:
            # Вместо редиректа на ту же страницу — показываем шаблон с ошибкой
            messages.error(request, f'Ошибка загрузки: код {response.status_code}')
            return render(request, 'repairs.html', context)
            
    except requests.exceptions.ConnectionError:
        messages.error(request, 'Не удалось подключиться к серверу')
        return render(request, 'repairs.html', context)
    except Exception as e:
        messages.error(request, f'Ошибка repairs_detail: {str(e)}')
    return render(request, 'repairs.html', context)

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
                print(response.json())
                messages.error(request, 'Ошибка при загрузке данных')
                return redirect('repairs')
    except requests.exceptions.ConnectionError:
        messages.error(request, 'Не удалось подключиться к серверу')
        return redirect('repairs')
    except Exception as e:
        messages.error(request, f'Ошибка repair_delete: {str(e)}')
        return redirect('repairs')
    return render(request, 'repairs.html')



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
                messages.error(request, 'Аренда не найден')
                return redirect('repairs')
            else:
                print(response.json())
                messages.error(request, 'Ошибка при загрузке данных')
                return redirect('repairs')
    except requests.exceptions.ConnectionError:
        messages.error(request, 'Не удалось подключиться к серверу')
        return redirect('repairs')
    except Exception as e:
        messages.error(request, f'Ошибка repair_complete: {str(e)}')
        return redirect('repairs')
    return render(request, 'repairs.html')

# сотрудники
def staff(request):
    headers = get_headers(request)
    role = get_role(request)
    context = {}
    try:
        if headers:
                response = requests.get(
                    f'{FASTAPI_BASE_URL}/staff/get_staff_all', 
                    headers=headers,
                    timeout=10
                )
                staff_list = response.json()
                context={
                    'staff_list': staff_list,
                    'role' : role
                }
    except requests.exceptions.ConnectionError:
        messages.error(request, 'Не удалось подключиться к серверу')
        return redirect('staff')
    except Exception as e:
        messages.error(request, f'Ошибка staff: {str(e)}')
        return redirect('staff')
    return render(request, 'staff.html', context)

def staff_create(request):
    headers = get_headers(request)
    
    if not headers:
        messages.error(request, 'Ошибка авторизации')
        return redirect('login')

    # ===== POST-запрос: обрабатываем отправку формы =====
    if request.method == 'POST':
        # Получаем данные из формы
#         {
#   "username": "string",
#   "full_name": "string",
#   "email": "string",
#   "phone": "string",
#   "position": "manager",
#   "password": "string"
# }
        username = request.POST.get('username')
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        position = request.POST.get('position')
        password = request.POST.get('password')

        # Валидация
        if not all([username, full_name, email, phone, position, password]):
            messages.error(request, 'Заполните все поля')
            return redirect('repairs_create')
        

        staff_data = {
            "username": username,
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "position": position,
            "password": password
        }
        
        try:
            response = requests.post(
                f'{FASTAPI_BASE_URL}/staff/create_staff',
                json=staff_data,
                timeout=10,
                headers=headers
            )
            
            if response.status_code == 200:
                messages.success(request, 'Сотрудник успешно создан')
                return redirect('staff')
            elif response.status_code == 409 or response.status_code == 422:
                error = response.json()
                messages.error(request, f'Ошибка: {error["error"]}')
                return redirect('staff')
            elif response.status_code == 401:
                return redirect('login')
            else:
                print(response.json())
                error_msg = response.json().get('detail', 'Неизвестная ошибка')
                messages.error(request, f'Ошибка: {error_msg}')
                
        except requests.exceptions.ConnectionError:
            messages.error(request, 'Не удалось подключиться к серверу FastAPI')
        except Exception as e:
            messages.error(request, f'Ошибка staff_create: {str(e)}')
        
        return redirect('staff')
    return render(request, 'staff_create.html')
    


def staff_detail(request, pk):
    headers = get_headers(request)
    role = get_role(request)
    sub = get_sub(request)
    context = {}
    try:
        if headers:
                response = requests.get(
                    f'{FASTAPI_BASE_URL}/staff/get_staff_by_id/{pk}', 
                    params={'id': pk},
                    headers=headers,
                    timeout=10
                )

                response_staff = requests.get(
                    f'{FASTAPI_BASE_URL}/rental/get_rent_by_staff_id', 
                    params={'staff_id': pk},
                    headers=headers,
                    timeout=10
                )
                if response.status_code == 200 and response_staff.status_code == 200:
                    if response_staff.json() == {"error": "Не найдено"}:
                        staff_rentals = []
                    else:
                        staff_rentals = response_staff.json()
                    staff = response.json()
                    context={
                        'staff': staff,
                        "staff_rentals" : staff_rentals,
                        'sub': sub,
                        'role' : role
                    }
                        
    except requests.exceptions.ConnectionError:
        messages.error(request, 'Не удалось подключиться к серверу')
        return redirect('staff')
    except Exception as e:
        messages.error(request, f'Ошибка staff_detail: {str(e)}')
        return redirect('staff')
    return render(request, 'staff_detail.html', context)


def staff_delete(request, pk):
    headers = get_headers(request)
    
    if not headers:
        messages.error(request, 'Ошибка авторизации')
        return redirect('staff')
    
    try:
        response = requests.delete(
            f'{FASTAPI_BASE_URL}/staff/delete_staff',
            params={'staff_id': int(pk)},
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            messages.success(request, f'Сотрудник #{pk} успешно удалён')
            return redirect('staff')
        elif response.status_code == 401:
            return redirect('login')
        elif response.status_code == 404:
            messages.error(request, 'Сотрудник не найден')
            return redirect('staff')
        else:
            error_msg = response.json().get('detail', 'Неизвестная ошибка')
            messages.error(request, f'Ошибка: {error_msg}')
            print(response.json())
            return redirect('staff')
            
    except requests.exceptions.ConnectionError:
        messages.error(request, 'Не удалось подключиться к серверу FastAPI')
        return redirect('staff')
    except Exception as e:
        messages.error(request, f'Ошибка в staff_delete: {str(e)}')
        return redirect('staff')


# профиль
def infome(request):
    headers = get_headers(request)
    
    if not headers:
        messages.error(request, 'Ошибка авторизации')
        return redirect('login')
    
    try:
        # 1. Получаем информацию о текущем пользователе
        response = requests.get(
            f'{FASTAPI_BASE_URL}/staff/info_me',
            headers=headers,
            timeout=10
        )

        if response.status_code == 401:
            return redirect('login')
        
        if response.status_code != 200:
            messages.error(request, 'Не удалось загрузить профиль')
            return render(request, 'infome.html', {'error': True})
        
        infome = response.json()
        
        if infome['roles'][0] == 'manager':
            messages.warning(request, 'Не достаточно прав для полных данных')
            return render(request, 'infome.html', {'error': True})

        # 2. Получаем список всех сотрудников
        response_staff = requests.get(
            f'{FASTAPI_BASE_URL}/staff/get_staff_all', 
            headers=headers,
            timeout=10
        )
        
        if response_staff.status_code != 200:
            messages.error(request, 'Не удалось загрузить данные сотрудников')
            return render(request, 'infome.html', {'error': True})
        
        data_staff = response_staff.json()
        
        # 3. Ищем текущего сотрудника
        current_staff = None
        for staff in data_staff.get('items', []):
            if staff.get('username') == infome.get('sub'):
                current_staff = staff
                break
        
        if not current_staff:
            messages.error(request, 'Сотрудник не найден')
            return render(request, 'infome.html', {'error': True})
        
        # 4. Формируем контекст
        context = {
            'username': infome.get('sub', 'Неизвестно'),
            'role': infome.get('roles', [''])[0] if infome.get('roles') else 'Нет роли',
            'full_name': current_staff.get('full_name', '—'),
            'email': current_staff.get('email', '—'),
            'position': current_staff.get('position', '—'),
            'staff_id': current_staff.get('staff_id'),
        }
        
        # 5. Получаем аренды сотрудника
        response_rent = requests.get(
            f'{FASTAPI_BASE_URL}/rental/get_rent_by_staff_id',
            params={'staff_id': context['staff_id']},
            headers=headers,
            timeout=10
        )
        
        if response_rent.status_code == 200:
            context['my_rentals'] = response_rent.json()
        else:
            context['my_rentals'] = {'items': []}
        
        return render(request, 'infome.html', context)
        
    except requests.exceptions.ConnectionError:
        messages.error(request, 'Не удалось подключиться к серверу')
        return render(request, 'infome.html', {'error': True})
    except Exception as e:
        print(f"Ошибка в infome: {e}")
        messages.error(request, f'Ошибка в infome: {str(e)}')
        return render(request, 'infome.html', {'error': True})
