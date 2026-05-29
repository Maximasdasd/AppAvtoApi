# Car Rental Management System (AppAvtoApi)

Система управления автопрокатом из двух сервисов: **FastAPI** (бэкенд с бизнес-логикой и БД) и **Django** (веб-интерфейс с формами и страницами). Django общается с FastAPI по HTTP, авторизация — через JWT.

-----

## Архитектура

```
┌────────────────┐      HTTP + JWT       ┌────────────────────┐
│  Django (web)  │ ───────────────────►  │  FastAPI (backend) │
│  формы, шаблоны│  ◄─────────────────── │  логика + БД       │
│  сессии, токен │      JSON-ответы      │  PostgreSQL        │
└────────────────┘                       └────────────────────┘
        :8001 (условно)                          :8000
```

- **FastAPI** хранит все данные в PostgreSQL, выдаёт REST API, проверяет роли и токены.
- **Django** не имеет собственной бизнес-БД (только служебный `sqlite3` для сессий) — он берёт данные из FastAPI через `requests` и рендерит HTML. Токен FastAPI хранится в сессии Django.

-----

## Технологии

**FastAPI-сервис**

- FastAPI, Uvicorn — веб-фреймворк и ASGI-сервер
- SQLModel / SQLAlchemy 2.0 — ORM
- PostgreSQL — основная база данных
- Pydantic 2 — валидация и сериализация
- Alembic — миграции
- JWT (python-jose) + bcrypt — аутентификация и хеширование паролей
- fastapi-pagination — пагинация списков

**Django-сервис**

- Django 5 — веб-интерфейс (server-side rendering)
- requests — обращения к FastAPI
- SQLite — только для служебных нужд Django (сессии)

-----

## Структура проекта

```
AppAvtoApi/
├── docker-compose.yml          # FastAPI + PostgreSQL
├── car_dashboard.html          # автономный дашборд (статичный)
│
├── fastapi_service/            # БЭКЕНД
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/                # миграции
│   ├── scripts/
│   │   ├── data_generate.py    # генерация фейковых данных
│   │   └── seed_data.py
│   ├── tests/
│   │   ├── conftest.py         # общие фикстуры
│   │   ├── test_api.py         # юнит-тесты (моки контроллеров)
│   │   └── test_integration.py # интеграционные тесты (SQLite)
│   └── app/
│       ├── main.py             # точка входа, регистрация роутов
│       ├── api/                # роуты (staff, client, car, rental, repair)
│       ├── controllers/        # бизнес-логика
│       ├── dependencies/       # DI-провайдеры контроллеров
│       ├── schemas/            # Pydantic-схемы запросов/ответов
│       ├── models/model.py     # таблицы БД (SQLModel)
│       ├── core/
│       │   ├── config.py       # настройки (env, JWT)
│       │   ├── security.py     # JWT, хеши, проверка ролей
│       │   └── global_handler.py # обработчики ошибок
│       └── db/db.py            # движок, сессии, создание админа
│
└── django_service/             # ФРОНТЕНД
    ├── manage.py
    ├── requirements.txt
    ├── db.sqlite3              # служебная БД Django (сессии)
    ├── django_service/         # настройки проекта
    │   ├── settings.py
    │   └── urls.py
    └── core/
        ├── views.py            # вьюхи: дашборд, CRUD-страницы
        ├── urls.py             # маршруты Django
        ├── fastapi_client.py   # логин в FastAPI, заголовки, токен
        └── templates/          # HTML-шаблоны
```

-----

## База данных

Основные таблицы (FastAPI / PostgreSQL):

|Таблица       |Назначение           |Ключевые поля                                                                      |
|--------------|---------------------|-----------------------------------------------------------------------------------|
|`staff`       |сотрудники           |`staff_id`, `username`, `password_hashed`, `position` (роль)                       |
|`client`      |клиенты проката      |`client_id`, `full_name`, `driver_license` (уник.), `passport` (уник.), `is_active`|
|`cars`        |автопарк             |`car_id`, `number_car` (уник.), `brand`, `category`, `is_available`, `daily_price` |
|`rental`      |аренды               |`rental_id`, `client_id`, `car_id`, `staff_id`, `status_rent`, `total_price`       |
|`repair`      |ремонты              |`repair_id`, `car_id`, `start_rep`, `end_rep`, `price_rep`                         |
|`eventlog`    |журнал событий       |`eventLog_id`, `operation`, `description`                                          |
|`refreshtoken`|refresh-токены сессий|`token_id`, `token`, `staff_id`, `is_revoked`                                      |

### Перечисления (enums)

- **Роли (`UserRole`)**: `manager`, `admin`, `director`
- **Статус машины (`CarStatus`)**: `available`, `rented`, `under_repair`
- **Категория (`CarCategory`)**: `ECONOMY`, `STANDARD`, `PREMIUM`, `LUX`
- **Статус аренды (`RentalStatus`)**: `active`, `completed`, `cancelled`

### Роли пользователей

- **Администратор (`admin`)** — полный доступ, кроме отчётности
- **Директор (`director`)** — полный доступ, включая отчётность
- **Менеджер (`manager`)** — работа с клиентами, авто, арендой, ремонтом

-----

## Установка и запуск

### Вариант 1. Docker (рекомендуется для FastAPI + PostgreSQL)

Из корня проекта:

```bash
docker-compose up --build
```

Поднимется FastAPI на `http://localhost:8000` и PostgreSQL (БД `AVTOprokat`, пользователь `postgres`, пароль `root`). Django при этом запускается отдельно (см. ниже).

### Вариант 2. Локальный запуск FastAPI

```bash
cd fastapi_service

# виртуальное окружение
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

Создайте файл `.env` в каталоге `fastapi_service/` (рядом с `app/`):

```env
BD_HOST=localhost
BD_USER=postgres
BD_PASSWORD=root
BD_NAME=AVTOprokat
SECRET_KEY=ваш_секрет
```

Создайте БД `AVTOprokat` в PostgreSQL, затем примените миграции. В `alembic.ini` укажите свой `sqlalchemy.url`:

```
postgresql://postgres:root@localhost:5432/AVTOprokat
```

```bash
alembic upgrade head
```

Запуск API (из каталога `app/`):

```bash
cd app
python -m main
```

При старте автоматически создаётся администратор:
**логин `qweqwe`, пароль `qwerty`**.

Документация после запуска:

- Swagger UI — <http://localhost:8000/docs>
- ReDoc — <http://localhost:8000/redoc>

### Вариант 3. Запуск Django-интерфейса

FastAPI должен быть уже запущен (Django ходит на `http://127.0.0.1:8000`).

```bash
cd django_service
pip install -r requirements.txt
python manage.py migrate          # служебные таблицы Django (сессии)
python manage.py runserver
```

Вход в систему: страница логина Django принимает логин/пароль сотрудника, под капотом логинится в FastAPI и сохраняет JWT в сессию.

### Генерация тестовых данных

```bash
# в fastapi_service переключить путь к .env в config.py при необходимости
python scripts/data_generate.py
```

-----

## Тестирование (FastAPI)

```bash
cd fastapi_service
pip install -r requirements.txt
pytest tests/ -v
```

- `tests/test_api.py` — **юнит-тесты**: контроллеры замоканы (`MagicMock`), реальная БД не используется. Проверяют роуты, коды ответов, валидацию.
- `tests/test_integration.py` — **интеграционные тесты**: реальное приложение поверх in-memory SQLite, запрос проходит весь стек (роут → контроллер → БД → ответ).
- `tests/conftest.py` — общие фикстуры. Не требует PostgreSQL: на время тестов БД подменяется на SQLite.

Запуск по отдельности:

```bash
pytest tests/test_api.py -v           # только юнит
pytest tests/test_integration.py -v   # только интеграционные
```

Оценка покрытия:

```bash
pytest tests/ --cov=app --cov-report=term-missing
```

-----

## REST API (FastAPI)

Все защищённые эндпоинты требуют заголовок `Authorization: Bearer <access_token>`.
Списочные ответы возвращаются с пагинацией (`items`, `total`, `page`, `size`, `pages`).

### Staff (`/staff`)

|Метод|Путь                         |Доступ        |Описание                                           |
|-----|-----------------------------|--------------|---------------------------------------------------|
|POST |`/staff/login_staff`         |все           |вход (form-data: username, password), выдаёт токены|
|POST |`/staff/create_staff`        |admin         |создать сотрудника                                 |
|GET  |`/staff/get_staff_all`       |admin         |список сотрудников                                 |
|GET  |`/staff/get_staff_by_id/{id}`|авториз.      |сотрудник по id                                    |
|GET  |`/staff/info_me`             |admin, manager|данные текущего пользователя из токена             |
|POST |`/staff/refresh_token`       |—             |ротация refresh-токена                             |
|POST |`/staff/refresh_token_revoke`|admin         |отозвать refresh-токен                             |

### Client (`/client`)

|Метод|Путь                        |Доступ        |Описание             |
|-----|----------------------------|--------------|---------------------|
|GET  |`/client/get_clients_all`   |admin, manager|список клиентов      |
|GET  |`/client/get_client/{id}`   |admin, manager|клиент по id         |
|POST |`/client/create_client`     |admin, manager|создать клиента (201)|
|PATCH|`/client/refresh_client{id}`|admin, manager|обновить клиента     |

### Car (`/car`)

|Метод |Путь                  |Доступ        |Описание                                      |
|------|----------------------|--------------|----------------------------------------------|
|GET   |`/car/get_cars_all`   |admin, manager|список машин                                  |
|GET   |`/car/get_car/{id}`   |admin, manager|машина по id                                  |
|POST  |`/car/create_car`     |admin, manager|создать машину (201)                          |
|DELETE|`/car/delete_car/{id}`|admin, manager|удалить машину (нельзя, если в аренде/ремонте)|

### Rental (`/rental`)

|Метод |Путь                                      |Доступ        |Описание                       |
|------|------------------------------------------|--------------|-------------------------------|
|GET   |`/rental/get_rental_all`                  |admin, manager|список аренд                   |
|POST  |`/rental/create_rental`                   |admin, manager|создать аренду (201)           |
|PATCH |`/rental/rent_complete?rent_id=`          |admin, manager|завершить аренду               |
|PATCH |`/rental/rent_cancelled?rent_id=`         |admin, manager|отменить аренду                |
|GET   |`/rental/get_rent_by_id?rent_id=`         |admin, manager|аренда по id                   |
|GET   |`/rental/get_rent_by_client_id?client_id=`|admin, manager|аренды клиента                 |
|GET   |`/rental/get_rent_by_car_id?car_id=`      |admin, manager|аренды по машине               |
|GET   |`/rental/get_rent_by_staff_id?staff_id=`  |admin, manager|аренды по сотруднику           |
|GET   |`/rental/get_rent_by_status?status_rent=` |admin, manager|аренды по статусу              |
|DELETE|`/rental/clear_list_rent`                 |admin         |очистить завершённые/отменённые|

### Repair (`/repair`)

|Метод |Путь                                    |Доступ        |Описание            |
|------|----------------------------------------|--------------|--------------------|
|GET   |`/repair/get_repair_all`                |admin, manager|список ремонтов     |
|POST  |`/repair/create_repair`                 |admin, manager|создать ремонт (201)|
|PATCH |`/repair/complete_repair?repair_id=`    |admin, manager|завершить ремонт    |
|GET   |`/repair/get_repair_by_id?repair_id=`   |admin, manager|ремонт по id        |
|GET   |`/repair/get_repair_car_by_id?car_id=`  |admin, manager|ремонты по машине   |
|DELETE|`/repair/delete_repair_by_id?repair_id=`|admin         |удалить ремонт      |
|DELETE|`/repair/all_delete_repair`             |admin         |удалить все ремонты |

-----

## Веб-интерфейс (Django)

|Страница      |URL               |Описание                                |
|--------------|------------------|----------------------------------------|
|Логин         |`/login_staff/`   |вход через FastAPI                      |
|Дашборд       |`/dashboard`      |сводка: клиенты, авто, аренды, ремонты  |
|Авто          |`/cars/`          |список, поиск, фильтр по статусу        |
|Карточка авто |`/cars/<id>/`     |детали + история аренд                  |
|Клиенты       |`/clients/`       |список, поиск, создание                 |
|Аренды        |`/rentals/`       |список + счётчики по статусам           |
|Создать аренду|`/rentals/create/`|форма (выбор клиента и свободной машины)|
|Ремонты       |`/repairs/`       |список, создание, завершение, удаление  |
|Сотрудники    |`/staff/`         |список, карточка, создание              |
|Профиль       |`/infome/`        |данные текущего пользователя            |

-----

## Конфигурация и безопасность

Настройки в `app/core/config.py`:

- `ACCESS_TOKEN_EXPIRE_MINUTES` — время жизни access-токена (по умолчанию 30 минут)
- `REFRESH_TOKEN_EXPIRE_DAYS` — время жизни refresh-токена (по умолчанию 30 дней)
- `ALGORITHM` — алгоритм JWT (`HS256`)

Безопасность:

- пароли хранятся в виде bcrypt-хешей;
- доступ к эндпоинтам разграничен по ролям;
- сессии используют access + refresh токены с возможностью отзыва.

-----

## Коды ответов

|Код|Значение                               |
|---|---------------------------------------|
|200|успешный запрос                        |
|201|успешное создание                      |
|400|ошибка в данных / бизнес-правило       |
|401|требуется авторизация / токен невалиден|
|403|недостаточно прав                      |
|404|ресурс не найден                       |
|409|конфликт (дубликат)                    |
|422|ошибка валидации                       |
|500|внутренняя ошибка сервера              |

-----

## Известные ограничения

- Часть эндпоинтов поиска при пустом результате возвращает нестандартный ответ — это учтено на стороне Django.
- Django-интерфейс рассчитан на запущенный и доступный FastAPI-сервис на `127.0.0.1:8000`.
- Для production-развёртывания вынесите секреты (`SECRET_KEY`, пароль БД) в переменные окружения и не храните их в репозитории.