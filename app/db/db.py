from sqlmodel import SQLModel, create_engine, text
from sqlalchemy.orm import sessionmaker
from models.model import Staff, Cars, Client, Rental, Repair, EventLog
from core.config import settings



try:
    engine = create_engine(settings.get_database_url())
    print("Подключение успешно!")
except Exception as e:
    print(f"Ошибка подключения: {e}")


def create_tables():
    try:
        SQLModel.metadata.create_all(engine)
        print(f"Созданые таблицы: {', '.join(SQLModel.metadata.tables)}")
    except Exception as e:
        print(f"Ошибка создания таблицы: {e} или бд не созданна")


def drop_tables():
    SQLModel.metadata.drop_all(engine)
    print("Таблицы удалены")



SessionLocal = sessionmaker(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    
    except Exception as exc:
        db.rollback()
        raise exc
    
    finally:
        db.close()

