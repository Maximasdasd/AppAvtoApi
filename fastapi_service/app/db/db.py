from sqlmodel import SQLModel, create_engine, text
from sqlalchemy.orm import sessionmaker
from models.model import Staff, Cars, Client, Rental, Repair, EventLog
from core.config import settings

# для админа
from models.model import Staff as StaffModel
from models.model import UserRole
from sqlalchemy import select
from core.security import get_password_hash

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

def create_admin():
    db = SessionLocal()
    check_admin = db.execute(select(StaffModel).where(StaffModel.username == "qweqwe")).scalar_one_or_none()
    if check_admin:
        print("админ уже создан")
    else:
        password_hashed = get_password_hash("qwerty")
        admin = StaffModel(
                username="qweqwe",
                full_name="admin",
                password_hashed=password_hashed,
                email="avtoprokat@gmail.com",
                phone="+79326166559",
                position=UserRole.ADMIN
        )
        db.add(admin)
        db.commit()
        print("АДМИН с логин:qweqwe паролем:qwerty успешно создан")



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

