from fastapi import APIRouter, HTTPException, Depends
from schemas.car import CarBase, CreateCar, CarResponse
from dependencies.car import get_controllers
from fastapi_pagination import Page
from controllers.car import CarController
from core.security import oauth2_scheme

from core.security import wrapprer_check_roles

router = APIRouter()

@router.get("/get_cars_all", response_model=Page[CarResponse])
def get_cars_all(controller: CarController = Depends(get_controllers),
                token: str = Depends(oauth2_scheme), 
                check_roles: str = Depends(wrapprer_check_roles(['admin', 'manager']))):
    return controller.get_all_car()

@router.get("/get_car/{id}")
def get_car(car_id: int, controller: CarController = Depends(get_controllers), 
            token: str = Depends(oauth2_scheme), 
            check_roles: str = Depends(wrapprer_check_roles(['admin', 'manager']))) -> CarResponse:
    return controller.get_car_by_id(car_id)

@router.post("/create_car", response_model=CarResponse, status_code=201)
def create_car(car_data: CreateCar, controller: CarController = Depends(get_controllers), 
               token: str = Depends(oauth2_scheme),
               check_roles: str = Depends(wrapprer_check_roles(['admin', 'manager']))):
    """Создание новой машины"""
    return controller.create_car(car_data)

@router.delete("/delete_car/{id}")
def delete_car(car_id: int, controller: CarController = Depends(get_controllers),
               token: str = Depends(oauth2_scheme),
               check_roles: str = Depends(wrapprer_check_roles(['admin', 'manager']))):
    """
    Удаление авто
    
    :param car_id: Описание
    :type car_id: int
    :param controller: Описание
    :type controller: CarController
    :param token: Описание
    :type token: str
    :param check_roles: Описание
    :type check_roles: str
    """
    return controller.delete_car(car_id)