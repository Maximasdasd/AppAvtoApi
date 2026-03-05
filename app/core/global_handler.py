from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from json import JSONDecodeError
from fastapi.exceptions import RequestValidationError 
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import psycopg2


def validation_exception_handler(_: Request, exc: RequestValidationError):
    """Простой обработчик ошибок валидации"""
    for exception in exc.errors():
        print(exception)
        if exception['type'] == 'string_too_short' or exception['type'] == 'string_too_long':
            return JSONResponse(
                status_code=422,
                content={
                    "success": False,
                    "error": {
                        "message": f"Некорректный JSON: проверьте синтаксис (кавычки, скобки, запятые)",
                        "type": "validation_error",
                        "status_code": 422
                    }
                }
            )
        elif exception['type'] == 'json_invalid':
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": {
                        "message": f"Ошибка декодирования json",
                        "type": "json_invalid",
                        "status_code": 400
                    }
                }
            )
        else:
                return JSONResponse(
                status_code=422,
                content={
                    "success": False,
                    "error": {
                        "message": f"Ошибка валидации данных в поле {exception} возможно неправильный тип",
                        "type": "validation_error",
                        "status_code": 422
                    }
                }
            )


def integrity_error_handler(_: Request, exc: IntegrityError) -> JSONResponse:
    """
    СИНХРОННЫЙ обработчик IntegrityError
    """
    
    # проверяем оригинальную ошибку PostgreSQL
    if exc.orig and isinstance(exc.orig, psycopg2.errors.UniqueViolation):
        error_msg = str(exc.orig)
        
        # проверяем конкретные constrain
        if "cars_number_car_key" in error_msg:
            detail = "Автомобиль с таким номером уже существует"
            status_code = 409
        elif "client_driver_license_key" in error_msg:
            detail = "Клиент с такими вод правами уже существует"
            status_code = 409
        elif "client_passport_key" in error_msg:
            detail = "Клиент с таким паспортом уже существует"
            status_code = 409
        else:
            detail = "Нарушение уникальности данных"
            status_code = 422
    
    elif exc.orig and isinstance(exc.orig, psycopg2.errors.NotNullViolation):
        detail = "Обязательное поле не заполнено"
        status_code = 422
    
    elif exc.orig and isinstance(exc.orig, psycopg2.errors.ForeignKeyViolation):
        detail = "Ссылка на несуществующий объект"
        status_code = 400
    
    else:
        detail = "Ошибка целостности данных"
        status_code = 422
    
    return JSONResponse(
        status_code=status_code,
        content={"error": f"{detail} ||||| {exc}"} # добавляем оригинальную ошибку PostgreSQL ТОЛЬКО ВО ВРЕМЯ РАЗРАБОТКИ
        )


def sqlalchemy_error_handler(_: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    СИНХРОННЫЙ обработчик SQLAlchemyError
    
    """
    

    detail = "Ошибка базы данных"
    
    return JSONResponse(
        status_code=503,
        content={"error": detail + ' ' + str(exc)}
    )



def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    СИНХРОННЫЙ обработчик HTTP исключений
    

    """
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )



def global_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """
    СИНХРОННЫЙ обработчик всех необработанных исключений
    
    """
    
    # определяем детали ошибки в зависимости от среды
    detail = "Внутренняя ошибка сервера"
    
    return JSONResponse(
        status_code=500,
        content={"error": detail}
    )






















# def error_handler(get_method=False):
#     """
#     декоратор обработчика ошибок
#         """
#     def decorator(func):
#         @wraps(func) # нужен чтобы докстринги не терялись
#         def wrapper(self, *args, **kwargs):
#             try:
#                 return func(self, *args, **kwargs)
#             except HTTPException as e:
#                 if not get_method:
#                     self.db.rollback()
#                 print("Декоратор обработки ошибок отработал успешо")
#                 raise e
            
#             except IntegrityError as e:
#                 if not get_method:
#                     self.db.rollback()

#                 print("Декоратор обработки ошибок отработал успешо")

#                 if e.orig and isinstance(e.orig, psycopg2.errors.UniqueViolation) and "cars_number_car_key" in str(e.orig):
#                     raise HTTPException(status_code=409, detail="Такой номер авто уже существует")
#                 elif e.orig and isinstance(e.orig, psycopg2.errors.UniqueViolation) and "client_driver_license_key" in str(e.orig):
#                     raise HTTPException(status_code=409, detail="Клиент с такими вод правами уже существует")
#                 elif e.orig and isinstance(e.orig, psycopg2.errors.UniqueViolation) and "client_passport_key" in str(e.orig):
#                     raise HTTPException(status_code=409, detail="Клиент с таким паспортом уже существует")
#                 elif e.orig and isinstance(e.orig, psycopg2.errors.NotNullViolation):
#                     raise HTTPException(status_code=422, detail="Пустое NOT NULL поле")
#                 elif e.orig and isinstance(e.orig, psycopg2.errors.ForeignKeyViolation):
#                     raise HTTPException(status_code=400, detail="Сломанная внешняя ссылка")
#                 else:
#                     raise HTTPException(status_code=422, detail="Другая ошибка целостности (проверьте формат и ограничения полей)")

#             except SQLAlchemyError as e:
#                 if not get_method:
#                     self.db.rollback()
#                 print("Декоратор обработки ошибок отработал успешо")
#                 raise HTTPException(status_code=503, detail=f"Database error (SQLAlchemyError): {str(e)}")
            
#             except Exception as e:
#                 if not get_method:
#                     self.db.rollback()
#                 print("Декоратор обработки ошибок отработал успешо")
#                 raise HTTPException(500, f'Ошибка (Exception){e}')
            
#         return wrapper
#     return decorator