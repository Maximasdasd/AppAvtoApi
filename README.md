О проекте
Car Rental Management API — это backend-приложение для системы управления автопрокатом автомобилей, построенное на FastAPI. Приложение предоставляет полный набор REST API для автоматизации всех бизнес-процессов проката: от регистрации клиентов и управления автопарком до обработки аренд, ремонтов и генерации аналитических отчетов.



Технологии
FastAPI 0.104.1 — современный, быстрый веб-фреймворк

PostgreSQL — реляционная база данных

SQLAlchemy 2.0.23 — ORM для работы с БД

Pydantic 2.5.0 — валидация данных и сериализация

JWT — аутентификация через токены

Uvicorn — ASGI-сервер



Структура проекта
appAvto/


Структура базы данных
Основные таблицы:
staff — сотрудники системы
staff_id (int, PK) — уникальный идентификатор сотрудника
username (str) — логин для входа
full_name (str) — полное имя сотрудника
password_hashed (str) — хешированный пароль
email (str) — электронная почта
phone (str) — контактный телефон
position (UserRole) — должность/роль (manager/admin/director)

clients — клиенты проката
client_id (int, PK) — уникальный идентификатор клиента
full_name (str) — полное имя клиента
driver_license (str) — номер водительского удостоверения (уникальный)
passport (str) — паспортные данные
address (str) — адрес проживания
created_at (datetime) — дата регистрации
is_active (bool) — статус активности

cars — автомобили автопарка
car_id (int, PK) — уникальный идентификатор автомобиля
number_car (str) — государственный регистрационный номер
brand (str) — марка автомобиля
color (str) — цвет автомобиля
year (int) — год выпуска
is_available (CarStatus) — статус доступности (available/rented/under_repair)
category (CarCategory) — категория автомобиля (ECONOMY/STANDARD/PREMIUM/LUX)
daily_price (float) — цена аренды за сутки

rentals — аренда автомобилей
rental_id (int, PK) — уникальный идентификатор аренды
client_id (int, FK → clients) — ссылка на клиента
car_id (int, FK → cars) — ссылка на автомобиль
staff_id (int, FK → staff) — ссылка на сотрудника, оформившего аренду
status_rent (RentalStatus) — статус аренды (completed/cancelled/active)
start_time (datetime) — время начала аренды
end_time (datetime) — время окончания аренды
total_hours (float) — общая продолжительность аренды в часах
total_price (float) — общая стоимость аренды

repairs — ремонты автомобилей
repair_id (int, PK) — уникальный идентификатор ремонта
car_id (int, FK → cars) — ссылка на автомобиль
start_rep (datetime) — дата начала ремонта
end_rep (datetime) — дата окончания ремонта
price_rep (float) — стоимость ремонта

eventlog — журнал событий системы
eventLog_id (int, PK) — уникальный идентификатор записи
event_time (datetime) — время события
operation (str) — тип операции
client_id (int, FK → clients, nullable) — ссылка на клиента (если применимо)
staff_id (int, FK → staff, nullable) — ссылка на сотрудника (если применимо)
description (str) — описание события



Аутентификация и авторизация
Роли пользователей:

Администратор (admin) — полный доступ кроме отчетности
Директор (director) — полный доступ с отчетностью
Пользователь (manager) — работа с клиентами, авто, арендой, ремонтом

Установка и запуск

1. Клонирование репозитория
git clone <ваш-репозиторий>
cd appAvto

2. Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac

venv\Scripts\activate     # Windows

3. Установка зависимостей
pip install -r requirements.txt

4. Настройка базы данных
Создайте файл .env в корневой папке:
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=ваш_пароль
POSTGRES_DB=tourism_db
SECRET_KEY=ваш_секретный_ключ

СДЕЛАТЬ ПОСЛЕ СОЗДАНИЯ БД!!!
ДЛЯ МИГРАЦИЙ!!
Откройте alembic.ini.
Найдите строку sqlalchemy.url.
Измените её на ваши параметры подключения:
PostgreSQL: postgresql://user:password@localhost:5432/dbname
MySQL: mysql+pymysql://user:password@localhost:3306/dbname

И ВВЕСТИ ДАННУЮ КОМАНДУ
alembic upgrade head


5. Запуск приложения
ИЗ ДИРЕКТОРИИ!!! appAvto\app
cd C:\Users\79000\Desktop\appAvto\app>
ЗАПУСК!!!
python -m main


6. (Только для разработчиков) создание миграции команда:
alembic revision --autogenerate -m "Название миграции(например что меняется)"
alembic upgrade head


Документация API
После запуска приложения доступны:

Swagger UI: http://localhost:8000/docs

ReDoc: http://localhost:8000/redoc




Конфигурация
Настройки в app/config.py:
ACCESS_TOKEN_EXPIRE_MINUTES — время жизни токена (по умолчанию 30 минут)

ALGORITHM — алгоритм шифрования JWT (HS256)

Проекция на разные среды (development, production)

Безопасность:
Пароли хранятся в хешированном виде (argon2)

JWT токены для аутентификации

Разделение прав доступа



Особенности реализации
Пагинация
Все списковые endpoints поддерживают пагинацию:

limit — количество записей на странице (максимум 100)




Обработка ошибок
Приложение возвращает информативные HTTP статусы:

200 — успешный запрос

201 — успешное создание

400 — ошибка в данных

401 — требуется авторизация

403 — недостаточно прав

404 — ресурс не найден

409 — конфликт данных

422 — ошибка валидации

500 — внутренняя ошибка сервера