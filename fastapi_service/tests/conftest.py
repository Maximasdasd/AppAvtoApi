"""
conftest.py — общие фикстуры для тестов Car Rental API.

Обслуживает оба набора тестов в каталоге tests/:
  * test_api.py         — юнит-тесты (свой self-contained app_client с MagicMock,
                          фикстуры отсюда ему не нужны);
  * test_integration.py — интеграционные тесты (используют фикстуры ниже).

Интеграционный подход: поднимаем реальное FastAPI-приложение, но БД заменяем
на in-memory SQLite (одно соединение на сессию тестов). Реальные роуты,
контроллеры, схемы и обработчики ошибок работают как в проде — мокаем только
подключение к БД и токен.

ВАЖНО: здесь НЕ вызывается SQLModel.metadata.clear() (в отличие от старого
conftest для юнит-тестов) — очистка метаданных ломает регистрацию моделей
и интеграционные тесты. Очистка не нужна, юнит-тесты от неё не зависят.
"""
import os
import sys

import pytest

# --- Пути и окружение (до импортов приложения) -----------------------------
APP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app")
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, APP_DIR)
sys.path.insert(0, ROOT_DIR)

# Настройки нужны на этапе импорта core.config.Settings
os.environ.setdefault("BD_PASSWORD", "test_password")
os.environ.setdefault("BD_NAME", "test_db")
os.environ.setdefault("BD_HOST", "localhost")
os.environ.setdefault("BD_USER", "postgres")
os.environ.setdefault("SECRET_KEY", "test_secret_key_for_tests")
os.environ.setdefault("DEBUG", "True")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from fastapi.testclient import TestClient

# Импорт моделей нужен, чтобы они зарегистрировались в metadata
import models.model as model  # noqa: F401
from models.model import (
    Staff, Cars, Client, CarCategory, CarStatus, UserRole, RentalStatus,
)
from core.security import get_password_hash

# db.db создаёт движок прямо на этапе импорта по URL из настроек.
# Заставляем настройки отдавать in-memory SQLite, чтобы тестам не требовался
# ни PostgreSQL, ни драйвер psycopg2.
from core.config import settings as _settings
type(_settings).get_database_url = lambda self: "sqlite://"


# --- Движок и таблицы -------------------------------------------------------
@pytest.fixture(scope="session")
def engine():
    """Одно in-memory SQLite-соединение на всю сессию тестов."""
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(eng)
    yield eng
    SQLModel.metadata.drop_all(eng)


@pytest.fixture
def db_session(engine):
    """Чистая БД для каждого теста: создаём таблицы, в конце сносим."""
    SQLModel.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Полная очистка между тестами — изоляция данных
        SQLModel.metadata.drop_all(engine)
        SQLModel.metadata.create_all(engine)


# --- Приложение с подменёнными зависимостями --------------------------------
@pytest.fixture
def app(db_session, engine):
    """
    Реальное приложение, но:
      * get_db   -> отдаёт тестовую in-memory сессию
      * oauth2   -> отдаёт настоящий JWT с ролью admin (guard'ы ролей при
        этом реально отрабатывают — токен декодируется штатно)

    db.db создаёт Postgres-движок на этапе импорта (в тестах его нет),
    поэтому до импорта main подменяем engine/SessionLocal на тестовый SQLite.
    """
    import db.db as db_module
    from sqlalchemy.orm import sessionmaker

    db_module.engine = engine
    db_module.SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

    from main import app as fastapi_app
    from db.db import get_db
    from core.security import oauth2_scheme, wrapprer_check_roles, create_access_token

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Валидный токен с ролью admin — на случай, если endpoint сам декодит токен
    test_token = create_access_token({"sub": "qweqwe"}, ["admin"])

    def override_oauth2():
        return test_token

    # wrapprer_check_roles вызывается как Depends(wrapprer_check_roles([...])),
    # т.е. возвращаемая функция check_roles используется как зависимость.
    # Чтобы не зависеть от хранения сгенерированной замыкания-функции, проще
    # переопределить саму проверку через dependency_overrides по ключу-функции.
    # Поэтому подменяем фабрику так, чтобы внутренняя зависимость всегда True.
    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[oauth2_scheme] = override_oauth2

    yield fastapi_app

    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def client(app):
    return TestClient(app, raise_server_exceptions=False)


# --- Хелперы для наполнения БД ---------------------------------------------
@pytest.fixture
def admin_staff(db_session):
    staff = Staff(
        username="qweqwe",
        full_name="admin",
        password_hashed=get_password_hash("qwerty"),
        email="admin@test.com",
        phone="+70000000000",
        position=UserRole.ADMIN,
    )
    db_session.add(staff)
    db_session.commit()
    db_session.refresh(staff)
    return staff


@pytest.fixture
def sample_car(db_session):
    car = Cars(
        number_car="A123BC",
        brand="Toyota",
        color="black",
        year=2020,
        is_available=CarStatus.AVAILABLE,
        category=CarCategory.STANDARD,
        daily_price=2400.0,
    )
    db_session.add(car)
    db_session.commit()
    db_session.refresh(car)
    return car


@pytest.fixture
def sample_client(db_session):
    c = Client(
        full_name="Иван Иванов",
        driver_license="1234567",
        passport="4500123456",
        address="Москва",
    )
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)
    return c


def make_access_token(role: str = "admin") -> str:
    from jose import jwt
    from datetime import datetime, timedelta, timezone
    payload = {
        "sub": "1",
        "roles": [role],
        "type": "access",
        "exp": int((datetime.now(timezone.utc) + timedelta(minutes=30)).timestamp()),
    }
    return jwt.encode(payload, "test_secret_key_for_tests", algorithm="HS256")


@pytest.fixture()
def app_client():
    """
    Каждый тест получает свежий TestClient и свежие моки контроллеров.
    Пагинируемые эндпоинты мокаются на уровне контроллера — возвращают
    уже готовый объект Page, чтобы не трогать реальную БД.
    """
    from main import app
    from core.security import oauth2_scheme, wrapprer_check_roles
    from dependencies.car import get_controllers
    from dependencies.client import get_controllers_client
    from dependencies.rental import get_controllers_rental
    from dependencies.repair import get_controllers_repair
    from dependencies.staff import get_controllers_staff

    token = make_access_token("admin")

    car_ctrl    = MagicMock()
    client_ctrl = MagicMock()
    rental_ctrl = MagicMock()
    repair_ctrl = MagicMock()
    staff_ctrl  = MagicMock()

    app.dependency_overrides[oauth2_scheme]                             = lambda: token
    app.dependency_overrides[wrapprer_check_roles(["admin"])]           = lambda: True
    app.dependency_overrides[wrapprer_check_roles(["admin", "manager"])]= lambda: True
    app.dependency_overrides[get_controllers]        = lambda: car_ctrl
    app.dependency_overrides[get_controllers_client] = lambda: client_ctrl
    app.dependency_overrides[get_controllers_rental] = lambda: rental_ctrl
    app.dependency_overrides[get_controllers_repair] = lambda: repair_ctrl
    app.dependency_overrides[get_controllers_staff]  = lambda: staff_ctrl

    with TestClient(app, raise_server_exceptions=False) as c:
        c.car_ctrl    = car_ctrl
        c.client_ctrl = client_ctrl
        c.rental_ctrl = rental_ctrl
        c.repair_ctrl = repair_ctrl
        c.staff_ctrl  = staff_ctrl
        yield c

    app.dependency_overrides.clear()