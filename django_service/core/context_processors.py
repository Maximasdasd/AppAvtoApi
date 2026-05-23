# core/context_processors.py
from core.fastapi_client import get_fastapi_token, get_headers
import requests

FASTAPI_BASE_URL = "http://127.0.0.1:8000"

def user_info(request):
    """Добавляет информацию о пользователе во все шаблоны"""
    context = {
        'username': 'Гость',
        'role': 'Не авторизован',
    }
    
    token = get_fastapi_token(request)
    if not token:
        return context
    
    headers = get_headers(request)
    if not headers:
        return context
    
    try:
        response = requests.get(
            f'{FASTAPI_BASE_URL}/staff/info_me',
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            infome = response.json()
            context['username'] = infome.get('sub', 'Пользователь')
            roles = infome.get('roles', [])
            context['role'] = roles[0] if roles else 'Сотрудник'
            
    except Exception as e:
        print(f"Ошибка получения info_me: {e}")
    
    return context