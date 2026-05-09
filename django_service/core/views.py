from django.shortcuts import render
from django.http import HttpResponse

def hello(request):
    return HttpResponse("Тестовый URL работает!")


def dashboard(request):
    # Пока передаём пустой или тестовый контекст, чтобы шаблон не ругался на отсутствие переменных
    context = {
        'total_client': 0,
        'total_rent': 0,
        'total_repair': 0,
        'total_cars': 0,
    }
    return render(request, 'dashboard.html', context)