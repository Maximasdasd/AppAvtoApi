from django.shortcuts import render, redirect
from core.fastapi_client import get_fastapi_token, auto_login_to_fastapi, get_headers
import requests
from django.contrib import messages
# для пагинации
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage, PageNotAnInteger
from django_service.settings import FASTAPI_BASE_URL
from core.views.utils import get_fastapi, get_role, get_sub, TokenExpired


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

        elif response_rent.status_code == 409 or response_rent.status_code == 422:
                error = response.json()
                messages.error(request, f'Ошибка: {error["error"]}')
                context['my_rentals'] = {'items': []}
                return render(request, 'infome.html', context)
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
