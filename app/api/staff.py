# api/staff.py
from fastapi import APIRouter, HTTPException, Depends, Request
from schemas.staff import StaffResponsePublic, StaffCreate, GetToken
from dependencies.staff import get_controllers_staff
from controllers.staff import StaffController
from fastapi_pagination import Page
router = APIRouter()

from core.security import wrapprer_check_roles
from fastapi.security import OAuth2PasswordRequestForm
# устаревшая
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# bearer_scheme = HTTPBearer(
#     bearerFormat="JWT",
#     description="Введите токен в формате: Bearer <ваш_токен>",
#     auto_error=False
# )

from core.security import oauth2_scheme

@router.get("/get_staff_all", response_model=Page[StaffResponsePublic])
def get_staff_all(controller: StaffController = Depends(get_controllers_staff), token: str = Depends(oauth2_scheme), check_roles: str = Depends(wrapprer_check_roles(['admin']))) -> Page[StaffResponsePublic]:
    """
    Вывод всех сотрудников
    
    :param controller: Описание
    :type controller: StaffController
    :param token: Описание
    :type token: str
    :param check_roles: Описание
    :type check_roles: str
    :return: Описание
    :rtype: Page[StaffResponsePublic]
    """
    return controller.get_all_staff()


@router.get("/get_staff_by_id/{id}", response_model=StaffResponsePublic)
def get_staff_all(id: int, controller: StaffController = Depends(get_controllers_staff),token: str = Depends(oauth2_scheme)) -> StaffResponsePublic:
    """
    Вывод всех сотрудников
    
    :param id: Описание
    :type id: int
    :param controller: Описание
    :type controller: StaffController
    :param token: Описание
    :type token: str
    :return: Описание
    :rtype: StaffResponsePublic
    """
    if not controller.get_staff_by_id(id):
        raise HTTPException(
            status_code=404,
            detail="Сотрудник не найден"
        )
    else:
        return controller.get_staff_by_id(id)
    

@router.post("/create_staff", response_model=StaffResponsePublic)
def create_staff(staff_data: StaffCreate, 
                 controller: StaffController = Depends(get_controllers_staff), 
                 token: str = Depends(oauth2_scheme), 
                 check_roles: str = Depends(wrapprer_check_roles(['admin']))) -> StaffResponsePublic:
    """
    Создание учетной записи сотрудника
    
    :param staff_data: Описание
    :type staff_data: StaffCreate
    :param controller: Описание
    :type controller: StaffController
    :param token: Описание
    :type token: str
    :param check_roles: Описание
    :type check_roles: str
    :return: Описание
    :rtype: StaffResponsePublic
    """
    return controller.create_staff(staff_data)

@router.delete("/delete_staff")
def delete_staff(staff_id: int,
                 controller: StaffController = Depends(get_controllers_staff),
                 token: str = Depends(oauth2_scheme), 
                 check_roles: str = Depends(wrapprer_check_roles(['admin']))):
    """
    Удаляет учетную запись сотрудника
    
    :param staff_id: Описание
    :type staff_id: int
    :param controller: Описание
    :type controller: StaffController
    :param token: Описание
    :type token: str
    :param check_roles: Описание
    :type check_roles: str
    """
    return controller.delete_staff(staff_id)

# staff_data: OAuth2PasswordRequestForm = Depends()
@router.post("/login_staff", response_model=GetToken)
def login_staff(form_data: OAuth2PasswordRequestForm = Depends(),  controller: StaffController = Depends(get_controllers_staff)):
    """
    Вход в учетную запись сотрудника
    
    :param form_data: Описание
    :type form_data: OAuth2PasswordRequestForm
    :param controller: Описание
    :type controller: StaffController
    :return: Описание
    :rtype: dict[str, str]
    """
    return controller.login_staff(form_data.username, form_data.password)


@router.post("/refresh_token")
def refresh_token_staff(token:str,  
                        controller: StaffController = Depends(get_controllers_staff)):
    """
    Покачто делает проверку рефреш ли это токен
    
    :param token: Описание
    :type token: str
    :param controller: Описание
    :type controller: StaffController
    """
    return controller.refresh_token(token)


@router.post("/refresh_token_revoke")
def refresh_token_staff(refresh_token:str,
                        token:str = Depends(oauth2_scheme),
                        controller: StaffController = Depends(get_controllers_staff), 
                        check_roles: str = Depends(wrapprer_check_roles(['admin']))):
    """
    ендпоинт для отмены рефреш токена (сессии)
    
    :param refresh_token: Описание
    :type refresh_token: str
    :param token: Описание
    :type token: str
    :param controller: Описание
    :type controller: StaffController
    :param check_roles: Описание
    :type check_roles: str
    """
    return controller.refresh_token_revoke(refresh_token)


@router.get("/info_me")
def info_me(request: Request, token: str = Depends(oauth2_scheme), 
            controller: StaffController = Depends(get_controllers_staff), 
            check_roles: str = Depends(wrapprer_check_roles(['admin', 'manager']))):
    """
    Информация о авторизованном сотруднике
    
    :param token: Описание
    :type token: str
    :param controller: Описание
    :type controller: StaffController
    """
    print({
            'method': request.method,
            'url': request.url,
            'host': request.client

        })
    payload = controller.info_me(token)
    return f'Аккаунт c username: {payload["sub"]}, role: {payload["roles"]}........{payload}'
