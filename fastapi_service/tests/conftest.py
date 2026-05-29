"""
conftest.py — общие настройки для интеграционных тестов
"""
import sys
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

# Добавляем пути
APP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app")
sys.path.insert(0, APP_DIR)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

# Переменные окружения
os.environ.setdefault("BD_PASSWORD", "test_password")
os.environ.setdefault("BD_NAME", "test_db")
os.environ.setdefault("BD_HOST", "localhost")
os.environ.setdefault("BD_USER", "postgres")
os.environ.setdefault("SECRET_KEY", "test_secret_key_for_tests")
os.environ.setdefault("DEBUG", "True")


@pytest.fixture(scope="session")
def engine():
    """Создаёт тестовую БД и очищает метаданные перед созданием таблиц"""
    # Очищаем метаданные перед созданием таблиц
    SQLModel.metadata.clear()
    
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(engine):
    """Создаёт свежую сессию для каждого теста"""
    connection = engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()