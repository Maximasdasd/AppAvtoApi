FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 8001, потому что Django делит сеть с FastAPI, а порт 8000 там уже занят FastAPI.
EXPOSE 8001

# migrate готовит локальную SQLite (сессии), затем поднимаем dev-сервер на 8001.
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py runserver 0.0.0.0:8001"]
