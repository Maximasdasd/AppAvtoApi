from models.model import Cars as CarsModel
from sqlalchemy import select
from fastapi_pagination.ext.sqlalchemy import paginate
from schemas.car import CreateCar, CarResponse
from fastapi import HTTPException
from sqlalchemy.orm import Session


class CarController:
    def __init__(self, db: Session):
        self.db = db

    def get_all_car(self):
        query = select(CarsModel).order_by(CarsModel.car_id)
        return paginate(self.db, query)
    

    def get_car_by_id(self, car_id: int) -> CarResponse:
        car = self.db.get(CarsModel, car_id)
        if car:
            return car
        else:
            raise HTTPException(status_code=404, detail="Машина не найдена")
    
    def delete_car(self, car_id: int):
        car = self.db.get(CarsModel, car_id)
        if car:
            if car.is_available=="under_repair" or car.is_available=="rented":
                raise HTTPException(status_code=400, detail="Нельзя удалить машину, которая находится в аренде или ремонте")
            
            self.db.delete(car)
            self.db.commit()
            return {"message": "Авто успешно удалено"}
        else:
            raise HTTPException(status_code=404, detail="Машина не найдена")

    def create_car(self, car_data: CreateCar):
            stmt = select(CarsModel).where(CarsModel.number_car == car_data.number_car)
            result = self.db.execute(stmt)
            check_number_car = result.scalars().first() 
            if check_number_car:
                raise HTTPException(status_code=409, detail="Такая машина уже существует")
            
            new_car = CarsModel(
                number_car=car_data.number_car,
                brand=car_data.brand,
                color=car_data.color,
                year=car_data.year,
                category=car_data.category,
                daily_price=car_data.daily_price
            )
            self.db.add(new_car)
            self.db.commit()
            return new_car
