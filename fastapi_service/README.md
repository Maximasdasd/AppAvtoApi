Car Rental API
Car Rental API — это backend-приложение для сервиса аренды автомобилей, построенное на FastAPI. Приложение предоставляет полный набор REST API для управления клиентами, автомобилями, сотрудниками, арендой, ремонтом и аутентификацией с ролевой моделью доступа.

Технологии
Технология	Версия	Назначение
FastAPI	0.104.1	Веб-фреймворк
SQLModel	-	ORM для работы с БД
PostgreSQL	-	Реляционная база данных
Pydantic	2.5.0	Валидация данных
JWT	-	Аутентификация через токены
Alembic	-	Миграции базы данных
Uvicorn	-	ASGI-сервер
FastAPI Pagination	-	Пагинация ответов
Структура проекта
text
AppAvtoApi/
├── fastapi_service/           # Основное приложение
│   ├── main.py                # Точка входа
│   ├── api/                   # Эндпоинты
│   │   ├── car.py
│   │   ├── client.py
│   │   ├── rental.py
│   │   ├── repair.py
│   │   └── staff.py
│   ├── controllers/           # Бизнес-логика
│   ├── schemas/               # Pydantic схемы
│   ├── dependencies/          # DI зависимости
│   ├── core/                  # Настройки и безопасность
│   │   ├── config.py          # Конфигурация
│   │   ├── security.py        # JWT, хеширование, роли
│   │   └── global_handler.py  # Глобальные обработчики ошибок
│   ├── db/                    # База данных
│   │   ├── db.py              # Подключение
│   │   └── models.py          # SQLModel модели
├── .env                       # Переменные окружения
└── requirements.txt           # Зависимости
Структура базы данных
Таблицы и поля
Таблица	Поля	Описание
client	client_id, full_name, driver_license, passport, address, created_at, is_active	Клиенты
staff	staff_id, username, full_name, password_hashed, email, phone, position	Сотрудники
cars	car_id, number_car, brand, color, year, is_available, category, daily_price	Автомобили
rental	rental_id, client_id, car_id, staff_id, status_rent, start_time, end_time, total_hours, total_price	Аренда
repair	repair_id, car_id, start_rep, end_rep, price_rep	Ремонт
eventlog	eventLog_id, event_time, operation, client_id, staff_id, description	Логи событий
refreshtoken	token_id, token, staff_id, expires_at, is_revoked, created_at	Refresh токены
Enum-типы
Enum	Значения
CarCategory	ECONOMY, STANDARD, PREMIUM, LUX
CarStatus	available, rented, under_repair
RentalStatus	active, completed, cancelled
UserRole	manager, admin, director
Аутентификация и авторизация
Роли пользователей
Роль	Доступ
admin	Полный доступ ко всем операциям
manager	Просмотр и управление арендой, клиентами, авто, ремонтом
director	Расширенные права (по необходимости)
Получение токена
http
POST /staff/login_staff
Content-Type: application/x-www-form-urlencoded

username=ваш_логин&password=ваш_пароль
Ответ:

json
{
  "access_token": "jwt_token",
  "refresh_token": "refresh_token",
  "token_type": "bearer"
}
Обновление токена
http
POST /staff/refresh_token?token=refresh_token_значение
Отзыв refresh токена
http
POST /staff/refresh_token_revoke?refresh_token=значение
Authorization: Bearer ваш_access_token
Основные API endpoints
1. Сотрудники (Staff)
Метод	Эндпоинт	Описание	Доступ
GET	/staff/get_staff_all	Список всех сотрудников	admin
GET	/staff/get_staff_by_id/{id}	Информация о сотруднике	admin
POST	/staff/create_staff	Создание сотрудника	admin
POST	/staff/login_staff	Вход в систему	public
POST	/staff/refresh_token	Обновление токена	public
POST	/staff/refresh_token_revoke	Отзыв refresh токена	admin
GET	/staff/info_me	Информация о текущем сотруднике	admin, manager
2. Клиенты (Client)
Метод	Эндпоинт	Описание	Доступ
GET	/client/get_clients_all	Список всех клиентов	admin, manager
GET	/client/get_client/{id}	Информация о клиенте	admin, manager
POST	/client/create_client	Создание клиента	admin, manager
PATCH	/client/refresh_client{id}	Обновление клиента	admin, manager
3. Автомобили (Car)
Метод	Эндпоинт	Описание	Доступ
GET	/car/get_cars_all	Список всех автомобилей (с пагинацией)	admin, manager
GET	/car/get_car/{id}	Информация об автомобиле	admin, manager
POST	/car/create_car	Создание автомобиля	admin, manager
DELETE	/car/delete_car/{id}	Удаление автомобиля	admin, manager
4. Аренда (Rental)
Метод	Эндпоинт	Описание	Доступ
GET	/rental/get_rental_all	Список всех аренд	admin, manager
POST	/rental/create_rental	Создание аренды	admin, manager
PATCH	/rental/rent_cancelled?rent_id={id}	Отмена аренды	admin, manager
PATCH	/rental/rent_complete?rent_id={id}	Завершение аренды	admin, manager
DELETE	/rental/clear_list_rent	Удаление завершенных аренд	admin
GET	/rental/get_rent_by_id?rent_id={id}	Аренда по ID	admin, manager
GET	/rental/get_rent_by_client_id?client_id={id}	Аренды клиента	admin, manager
GET	/rental/get_rent_by_car_id?car_id={id}	Аренды авто	admin, manager
GET	/rental/get_rent_by_staff_id?staff_id={id}	Аренды сотрудника	admin, manager
GET	/rental/get_rent_by_status?status_rent={status}	Аренды по статусу	admin, manager
Статусы аренды: ACTIVE, COMPLETED, CANCELLED

5. Ремонт (Repair)
Метод	Эндпоинт	Описание	Доступ
GET	/repair/get_repair_all	Список всех ремонтов	admin, manager
POST	/repair/create_repair	Создание ремонта	admin, manager
PATCH	/repair/complete_repair?repair_id={id}	Завершение ремонта	admin, manager
GET	/repair/get_repair_by_id?repair_id={id}	Ремонт по ID	admin, manager
GET	/repair/get_repair_car_by_id?car_id={id}	Ремонты авто	admin, manager
DELETE	/repair/delete_repair_by_id?repair_id={id}	Удаление ремонта	admin
DELETE	/repair/all_delete_repair	Удаление всех ремонтов	admin
Пагинация
Все list-эндпоинты поддерживают пагинацию через fastapi_pagination:

Используется Page[ModelResponse] в response_model

Параметры запроса: page и size (автоматически)

Обработка ошибок
Статус	Описание
200	Успешный запрос
201	Успешное создание
400	Ошибка в данных
401	Требуется авторизация
403	Недостаточно прав
404	Ресурс не найден
409	Конфликт данных (уникальность)
422	Ошибка валидации
500	Внутренняя ошибка сервера
Глобальные обработчики:

IntegrityError — нарушение уникальности

SQLAlchemyError — ошибки БД

RequestValidationError — ошибки валидации

Установка и запуск
1. Клонирование репозитория
bash
git clone https://github.com/Maximasdasd/AppAvtoApi.git
cd AppAvtoApi/fastapi_service
2. Создание виртуального окружения
bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
3. Установка зависимостей
bash
pip install -r requirements.txt
4. Настройка базы данных
Создайте файл .env в папке fastapi_service/:

env
BD_HOST=localhost
BD_USER=postgres
BD_PASSWORD=ваш_пароль
BD_NAME=car_rental_db

SECRET_KEY=ваш_секретный_ключ
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30
5. Запуск приложения
СДЕЛАТЬ ПОСЛЕ СОЗДАНИЯ БД!!!  
ДЛЯ МИГРАЦИЙ!!  
Откройте alembic.ini.  
Найдите строку sqlalchemy.url.  
Измените её на ваши параметры подключения:  
PostgreSQL: postgresql://user:password@localhost:5432/dbname 
MySQL: mysql+pymysql://user:password@localhost:3306/dbname  

И ВВЕСТИ ДАННУЮ КОМАНДУ  
alembic upgrade head


Запуск приложения  
API  
ИЗ ДИРЕКТОРИИ!!! appAvto\fastapi_service\app  
cd C:\Users\79000\Desktop\appAvto\fastapi_service\app>  
ЗАПУСК!!!  
python -m main


(Только для разработчиков) создание миграции команда:  
alembic revision --autogenerate -m "Название миграции(например что меняется)"  
alembic upgrade head


для вставки фейк данных (тестирования) или для докера  
Необходимо поменять в файле config переменную к пути .env файла  
тк для фейк данных или докера запускается с другой директории

bash
python main.py


При запуске автоматически:

Создаются все таблицы

Создается admin-пользователь (если не существует)

Документация API
После запуска доступны:

Swagger UI: http://localhost:8000/docs

ReDoc: http://localhost:8000/redoc

Конфигурация
Основные настройки (core/config.py)
Параметр	Значение по умолчанию	Описание
ACCESS_TOKEN_EXPIRE_MINUTES	30	Время жизни access токена
REFRESH_TOKEN_EXPIRE_DAYS	30	Время жизни refresh токена
ALGORITHM	HS256	Алгоритм шифрования JWT
Безопасность
Пароли хранятся в хешированном виде (Passlib + bcrypt)

JWT токены для аутентификации

Refresh токены с возможностью отзыва

Ролевая модель доступа через декоратор wrapprer_check_roles

Особенности реализации
Асинхронность — все эндпоинты асинхронные

Пагинация — встроенная поддержка через fastapi_pagination

Глобальная обработка ошибок — кастомные хендлеры для всех типов исключений

Refresh token механизм — поддержка сессий с возможностью отзыва

Middleware (закомментирован) — готовый аудит запросов

Команды для разработки
bash
# Создание всех таблиц (автоматически при запуске)
python -c "from db.db import create_tables; create_tables()"

# Удаление всех таблиц
python -c "from db.db import drop_tables; drop_tables()"

# Создание admin пользователя
python -c "from db.db import create_admin; create_admin()"
Лицензия
Проект разработан для внутреннего использования.

API Version: 1.0.0
Последнее обновление: 2026