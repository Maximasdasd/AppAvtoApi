from fastapi import FastAPI, APIRouter, Request
# Импорт роутеров
from api.staff import router as staff_router
from api.client import router as client_router
from api.car import router as car_router
from api.rental import router as rental_router
from api.repair import router as repair_router
# from controllers.eventLog import router as eventLog_router

from db.db import create_tables, drop_tables
from fastapi_pagination import add_pagination
from core.security import oauth2_scheme

# error
from core.global_handler import integrity_error_handler, sqlalchemy_error_handler, http_exception_handler, global_exception_handler, validation_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi.exceptions import RequestValidationError


# Создаем приложение
app = FastAPI(
    title="Car Rental API",
    version="1.0.0",
    description="API для аренды автомобилей",
)



app.include_router(staff_router, prefix="/staff",tags=["Staff"])
app.include_router(client_router, prefix="/client", tags=["Client"])
app.include_router(car_router, prefix="/car", tags=["Car"])
app.include_router(rental_router, prefix="/rental", tags=["Rental"])
app.include_router(repair_router, prefix="/repair", tags=["Repair"])

add_pagination(app)

# error
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)


# @app.middleware("http")
# async def audit_middleware(request: Request, call_next):
#     """
#     Асинхронный middleware (обязательно async/await!)
#     """
#     # 1. Получаем endpoint (для docstring, если нужно)
#     route = request.scope.get("route")
#     route_handler = route.endpoint if route else None

#     # 2. Формируем название операции
#     operation = request.method + "_" + request.url.path.replace('/', '_').strip('_')

#     # 3. Путь запроса
#     path = str(request.url.path)

#     # 4. Заголовок авторизации
#     auth_header = request.headers.get("authorization")

#     # 5. IP-адрес клиента
#     client_ip = request.client.host if request.client else "unknown"

#     # 6. Вызываем следующий обработчик (обязательно с await!)
#     response = await call_next(request)

#     # 7. Логируем информацию
#     print(f"[SYNC AUDIT] {operation} | IP: {client_ip} | Auth: {auth_header}")

#     # 8. Возвращаем ответ
#     return response

# Корневой эндпоинт
@app.get("/")
def root():
    return {
        "message": "Car Rental API",
        "docs": "/docs",
        "version": "1.0.0"
    }



if __name__ == "__main__":
    # drop_tables()
    create_tables()
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

