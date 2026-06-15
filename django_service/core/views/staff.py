from django.shortcuts import render, redirect
from core.fastapi_client import get_fastapi_token, auto_login_to_fastapi, get_headers
import requests
from django.contrib import messages
# для пагинации
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage, PageNotAnInteger
from django_service.settings import FASTAPI_BASE_URL
from core.views.utils import get_fastapi, get_role, get_sub, TokenExpired



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
    return render(request, 'staff/staff.html', context)

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
            return redirect('staff_create')
        

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
            
            if response.status_code == 201:
                messages.success(request, 'Сотрудник успешно создан')
                return redirect('staff')
            elif response.status_code == 409 or response.status_code == 422:
                error = response.json()
                messages.error(request, f'Ошибка: {error["error"]}')
                return redirect('staff')
            elif response.status_code == 401:
                return redirect('login')
            else:
                error_msg = response.json().get('detail', 'Неизвестная ошибка')
                messages.error(request, f'Ошибка: {error_msg}')
                
        except requests.exceptions.ConnectionError:
            messages.error(request, 'Не удалось подключиться к серверу FastAPI')
        except Exception as e:
            messages.error(request, f'Ошибка staff_create: {str(e)}')
        
        return redirect('staff')
    return render(request, 'staff/staff_create.html')
    


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
    return render(request, 'staff/staff_detail.html', context)
