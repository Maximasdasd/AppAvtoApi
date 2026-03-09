# api/client.py
from fastapi import APIRouter, HTTPException, Depends
from schemas.client import ClientResponse, ClientCreate
from dependencies.client import get_controllers_client
from controllers.client import ClientController
from fastapi_pagination import Page
from core.security import oauth2_scheme

from core.security import wrapprer_check_roles

router = APIRouter()

# test
@router.get("/get_clients_all", response_model=Page[ClientResponse])
def get_client_all(token: str = Depends(oauth2_scheme), 
                   controller: ClientController = Depends(get_controllers_client), 
                   check_roles: str = Depends(wrapprer_check_roles(['admin', 'manager']))) -> Page[ClientResponse]:
    """Вывод всех клиентов"""
    return controller.get_client()

@router.get("/get_client/{id}")
def get_client(id: int, 
               controller: ClientController = Depends(get_controllers_client), 
               token: str = Depends(oauth2_scheme), 
               check_roles: str = Depends(wrapprer_check_roles(['admin', 'manager']))) -> ClientResponse:
    """Получение одного клиента"""
    if not controller.get_client_by_id(id):
        raise HTTPException(status_code=404, detail="Клиент не найден")
    else:
        return controller.get_client_by_id(id)

@router.post("/create_client", response_model=ClientResponse, status_code=201)
def create_client(client_data: ClientCreate, 
                  controller: ClientController = Depends(get_controllers_client), 
                  token: str = Depends(oauth2_scheme), 
                  check_roles: str = Depends(wrapprer_check_roles(['admin', 'manager']))) -> ClientResponse:
    """Создание нового клиента"""
    return controller.create_client(client_data)

@router.patch("/refresh_client{id}",response_model=ClientResponse, status_code=201)
def refresh_client(client_new_data:ClientCreate, client_id, controller: ClientController = Depends(get_controllers_client), 
                       token: str = Depends(oauth2_scheme), 
                       check_roles: str = Depends(wrapprer_check_roles(['admin', 'manager']))) -> ClientResponse:
    """Обновление Клиента"""
    return controller.refresh_client(client_new_data, client_id)



@router.delete("/delete_all_clients", status_code=200)
def delete_all_clients(controller: ClientController = Depends(get_controllers_client), 
                       token: str = Depends(oauth2_scheme), 
                       check_roles: str = Depends(wrapprer_check_roles(['admin']))) -> dict:
    """Удаление всех клиентов"""
    return controller.delete_all_clients()

