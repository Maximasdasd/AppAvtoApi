FROM python:3.10.20-slim
WORKDIR /app


COPY requirements.txt .
RUN pip install -r requirements.txt


COPY .env ./
COPY app/. ./
COPY alembic.ini ./
COPY alembic/ ./alembic/

ENTRYPOINT ["python", "-m", "main"]
