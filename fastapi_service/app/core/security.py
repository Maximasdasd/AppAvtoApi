from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import HTTPException
from core.config import settings
import bcrypt

from fastapi import Depends

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/staff/login_staff")

# создлать через passlib так как оно провряет лучше и защищает лучше миграции алгоритмов можно сделать

def get_password_hash(password: str) -> str:
    """Хэширование пароля"""
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password, hashed_password):
    if bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8")):
        return True
    else:
        return False

def create_access_token(
    data: dict,
    roles: list[str] | None = None,  # Добавляем параметр для ролей
) -> str:
    
    to_encode = data.copy()


    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp":int(expire.timestamp())})
    to_encode.update({"type": 'access'})

    if roles:
        to_encode.update({"roles": roles})

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp":int(expire.timestamp())})

    to_encode.update({"type": 'refresh'})

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Неверный токен или токен истек")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Токен истёк {e}")
    
# def check_roles(token: str, roles: list[str]) -> bool:
#     if token:
#         payload = decode_token(token)
#         if payload['roles'] == roles:
#             return True
#         else:
#             raise HTTPException(status_code=401, detail="Недостаточно прав")


def current_user(payload:str = Depends(oauth2_scheme)):
    if payload:
        payload = decode_token(payload)
        return payload

def wrapprer_check_roles(roles:dict):
    def check_roles(payload:str = Depends(current_user)) -> bool:
        if payload:
            if payload['roles'][0] in roles:
                return True
            else:
                raise HTTPException(status_code=401, detail="Недостаточно прав")
        else:
            raise HTTPException(status_code=401, detail="Нет данных пользователя")
    return check_roles
