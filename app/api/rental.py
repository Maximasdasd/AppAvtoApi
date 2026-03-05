from fastapi import APIRouter, HTTPException, Depends
from schemas.rental import RentalResponse, RentCreate
from dependencies.rental import get_controllers_rental
from controllers.rental import RentalController
from fastapi_pagination import Page
from core.security import oauth2_scheme, wrapprer_check_roles


router = APIRouter()

@router.get("/get_rental_all", response_model=Page[RentalResponse])
def get_rental_all(controller: RentalController = Depends(get_controllers_rental), token: str = Depends(oauth2_scheme), check_roles: str = Depends(wrapprer_check_roles(['admin', 'manager']))):
    return controller.get_all_rent()


@router.post("/create_rental", status_code=201, response_model=RentalResponse)
def create_rental(rent_data: RentCreate, 
                  controller: RentalController = Depends(get_controllers_rental), 
                  token: str = Depends(oauth2_scheme), 
                  check_roles: str = Depends(wrapprer_check_roles(['admin', 'manager']))):
    return controller.create_rent(rent_data, token)

@router.patch("/rent_cancelled")
def rent_cancelled(rent_id: int,
                   controller: RentalController = Depends(get_controllers_rental), 
                  token: str = Depends(oauth2_scheme), 
                  check_roles: str = Depends(wrapprer_check_roles(['admin', 'manager']))):
    return controller.rent_cancelled(rent_id)


@router.patch("/rent_complete")
def rent_complete(rent_id: int,
                  controller: RentalController = Depends(get_controllers_rental), 
                  token: str = Depends(oauth2_scheme), 
                  check_roles: str = Depends(wrapprer_check_roles(['admin', 'manager']))):
    return controller.rent_complete(rent_id)


@router.delete("/clear_list_rent")
def clear_list_rent(controller: RentalController = Depends(get_controllers_rental), 
                  token: str = Depends(oauth2_scheme), 
                  check_roles: str = Depends(wrapprer_check_roles(['admin']))):
        # только завершенные аренды
    return controller.clear_list_rent()


@router.get("/get_rent_by_id")
def get_rent_by_id(rent_id: int,
                   controller: RentalController = Depends(get_controllers_rental), 
                  token: str = Depends(oauth2_scheme), 
                  check_roles: str = Depends(wrapprer_check_roles(['admin', 'manager']))):
    return controller.get_rent_by_id(rent_id)


@router.get("/get_rent_by_client_id", response_model=Page[RentalResponse])
def get_rent_by_client_id(client_id: int,
                          controller: RentalController = Depends(get_controllers_rental), 
                  token: str = Depends(oauth2_scheme), 
                  check_roles: str = Depends(wrapprer_check_roles(['admin', 'manager']))):
    return controller.get_rent_by_client_id(client_id)


@router.get("/get_rent_by_car_id", response_model=Page[RentalResponse])
def get_rent_by_car_id(car_id: int, 
                       controller: RentalController = Depends(get_controllers_rental), 
                  token: str = Depends(oauth2_scheme), 
                  check_roles: str = Depends(wrapprer_check_roles(['admin', 'manager']))):
    return controller.get_rent_by_car_id(car_id)


@router.get("/get_rent_by_staff_id", response_model=Page[RentalResponse])
def get_rent_by_staff_id(staff_id: int, 
                         controller: RentalController = Depends(get_controllers_rental), 
                  token: str = Depends(oauth2_scheme), 
                  check_roles: str = Depends(wrapprer_check_roles(['admin', 'manager']))):
    return controller.get_rent_by_staff_id(staff_id)


@router.get("/get_rent_by_status", response_model=Page[RentalResponse])
def get_rent_by_status(status_rent: str,
                       controller: RentalController = Depends(get_controllers_rental), 
                  token: str = Depends(oauth2_scheme), 
                  check_roles: str = Depends(wrapprer_check_roles(['admin', 'manager']))):
    """
                "ACTIVE","COMPLETED","CANCELLED"
    """
    return controller.get_rent_by_status(status_rent)