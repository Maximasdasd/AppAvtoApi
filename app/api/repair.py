# api/repair.py
from fastapi import APIRouter, HTTPException, Depends, Request
from schemas.repair import RepairCreate, RepairResponse, RepairComplete
from dependencies.repair import get_controllers_repair
from controllers.repair import RepairController
from fastapi_pagination import Page
from schemas.repair import RepairCreate, RepairResponse
from core.security import wrapprer_check_roles, oauth2_scheme
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter()


@router.get("/get_repair_all", response_model=Page[RepairResponse])
def get_repair_all(controller: RepairController = Depends(get_controllers_repair),  
                   token: str = Depends(oauth2_scheme), 
                    check_roles: str = Depends(wrapprer_check_roles(['admin', 'manager']))):
    return controller.get_repair_all()

@router.post("/create_repair", status_code=201, response_model=RepairResponse)
def create_repair(repair_data:RepairCreate, controller: RepairController = Depends(get_controllers_repair),  
                   token: str = Depends(oauth2_scheme), 
                    check_roles: str = Depends(wrapprer_check_roles(['admin', 'manager']))):
    return controller.create_repair(repair_data)

@router.patch("/complete_repair")
def complete_repair(repair_id:int, repairComplete_data: RepairComplete, controller: RepairController = Depends(get_controllers_repair),  
                   token: str = Depends(oauth2_scheme), 
                    check_roles: str = Depends(wrapprer_check_roles(['admin', 'manager']))):
    return controller.return_repair(repair_id, repairComplete_data)


@router.get("/get_repair_by_id")
def get_repair_by_id(repair_id: int, 
                     controller: RepairController = Depends(get_controllers_repair),  
                   token: str = Depends(oauth2_scheme), 
                    check_roles: str = Depends(wrapprer_check_roles(['admin', 'manager']))) -> RepairResponse:
    return controller.get_repair_by_id(repair_id)


@router.get("/get_repair_car_by_id", response_model=Page[RepairResponse])
def get_repir_car_id(car_id: int,
                     controller: RepairController = Depends(get_controllers_repair),  
                   token: str = Depends(oauth2_scheme), 
                    check_roles: str = Depends(wrapprer_check_roles(['admin', 'manager']))):
    return controller.get_repir_car_id(car_id)


@router.delete("/delete_repair_by_id")
def delete_repair_by_id(repair_id: int, 
                        controller: RepairController = Depends(get_controllers_repair),  
                   token: str = Depends(oauth2_scheme), 
                    check_roles: str = Depends(wrapprer_check_roles(['admin']))):
    return controller.delete_repair_by_id(repair_id)


@router.delete("/all_delete_repair")
def delete_all_repair(controller: RepairController = Depends(get_controllers_repair),  
                   token: str = Depends(oauth2_scheme), 
                    check_roles: str = Depends(wrapprer_check_roles(['admin']))):
    return controller.delete_repair_all()