from django.shortcuts import render, redirect
from core.fastapi_client import get_fastapi_token, auto_login_to_fastapi, get_headers
import requests
from django.contrib import messages
# для пагинации
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage, PageNotAnInteger
from django_service.settings import FASTAPI_BASE_URL

class TokenExpired(BaseException):
    pass

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
