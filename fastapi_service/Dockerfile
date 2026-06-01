FROM python:3.10-slim

# Логи сразу в stdout, без .pyc файлов
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Зависимости отдельным слоем (кеш)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Код приложения. app/. кладём прямо в /app,
# поэтому импорты вида `from core.config import settings` работают.
COPY app/. ./
COPY alembic.ini ./
COPY alembic ./alembic/

EXPOSE 8000

# main.py при запуске сам создаёт таблицы (create_tables) и админа (create_admin),
# затем поднимает uvicorn на 0.0.0.0:8000.
# .env НЕ копируем — все настройки приходят через переменные окружения из docker-compose.
CMD ["python", "-m", "main"]
