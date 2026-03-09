from fastapi import HTTPException, Request
from sqlalchemy import select, delete, exists
from fastapi_pagination.ext.sqlalchemy import paginate
from schemas.repair import RepairCreate, RepairResponse, RepairComplete
from models.model import Repair as RepairModel 
from sqlalchemy.orm import Session
from models.model import Cars as СarsModel
from models.model import CarStatus
from datetime import datetime, timezone

class RepairController:
    def __init__(self, db: Session):
        self.db = db
    
    def get_repair_all(self):
        query = select(RepairModel).order_by(RepairModel.repair_id)
        exec = self.db.execute(query).scalars().all()
        if exec is None:
            return HTTPException(status_code=404, detail="Ничего не найдено")
        return paginate(self.db, query)

    def create_repair(self, repair_data: RepairCreate):
        search_car = self.db.execute(select(СarsModel.is_available).where(СarsModel.car_id == repair_data.car_id)).scalar_one_or_none()
        if search_car is None:
            raise HTTPException(status_code=404, detail="Автомобиль не найден")
        
        if repair_data.price_rep < 0:
            raise HTTPException(status_code=400, detail="Цена не может быть меньше нуля")
        
        car_is_repair = self.db.get(СarsModel, repair_data.car_id)
        if car_is_repair.is_available == CarStatus.UNDER_REPAIR:
            raise HTTPException(status_code=400, detail="Автомобиль уже в ремонте")
        elif car_is_repair.is_available == CarStatus.RENTED:
            raise HTTPException(status_code=400, detail="Автомобиль находится в аренде")
        car_is_repair.is_available = CarStatus.UNDER_REPAIR

        Rent = RepairModel(
                car_id=repair_data.car_id,
                start_rep=repair_data.start_rep,
                price_rep=repair_data.price_rep,
            )


        self.db.add(Rent)
        self.db.commit()

        return Rent

    def return_repair(self, repair_id: int, repairComplete_data: RepairComplete):
        search_repair = self.db.get(RepairModel, repair_id)


        if search_repair is None:
            raise HTTPException(status_code=404, detail="Ремонт не найден")
        
        if search_repair.end_rep is None:
            # .replace(tzinfo=timezone.utc) нужен для того чтобы привести к одному формату даты тк из бд достается другой формат даты
            timedelta = repairComplete_data.end_rep - search_repair.start_rep.replace(tzinfo=timezone.utc)
            total_hours = timedelta.total_seconds()/3600
            print(total_hours)
            if total_hours > 0:
                search_repair.end_rep = repairComplete_data.end_rep
                car_is_repair = self.db.get(СarsModel, search_repair.car_id)
                car_is_repair.is_available = CarStatus.AVAILABLE
                self.db.commit()
                return {"message": "Ремонт завершен"}
            else:
                raise HTTPException(status_code=400, detail="Ремонт не может закончиться раньше начала")
        else:
            raise HTTPException(status_code=400, detail="Ремонт уже закончен")


    def get_repair_by_id(self, repair_id: int) -> RepairResponse:
        repair = self.db.execute(select(RepairModel).where(RepairModel.repair_id == repair_id)).scalars().first()
        if repair:
            return repair
        else:
            raise HTTPException(status_code=404, detail="Ремонт не найден с таким id")

    def get_repir_car_id(self, car_id: int):
        query_car_id = select(RepairModel).where(RepairModel.car_id == car_id)
        repair_car_id = self.db.execute(query_car_id).scalars().first()
        if repair_car_id:
            return paginate(self.db, query_car_id)
        else:
            raise HTTPException(status_code=404, detail="Ремонт не найден с таким car_id")

    def delete_repair_by_id(self, repair_id: int):
        repair_delete_list = self.db.execute(select(RepairModel).where(RepairModel.repair_id == repair_id)).scalars().first()
        if repair_delete_list:
            repair_id_delete = self.db.execute(delete(RepairModel).where(RepairModel.repair_id==repair_id))
            self.db.commit()
            return { "message":"Данные успешно удалены"}
        else:
            raise HTTPException(status_code=404, detail="Ремонт не найден с таким id")
        
    def delete_repair_all(self):
        result = self.db.execute(delete(RepairModel))
        deleted_count = result.rowcount
        if deleted_count == 0:
            raise HTTPException(status_code=404, detail="Список ремонта пуст")
        self.db.commit()
        return {
            "message": "Список ремонтов удалён",
            "deleted_count": deleted_count,
        }
