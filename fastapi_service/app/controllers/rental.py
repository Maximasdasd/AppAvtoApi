from fastapi import HTTPException
from sqlalchemy import select, delete, exists
from fastapi_pagination.ext.sqlalchemy import paginate
from schemas.rental import RentCreate, RentalResponse
from models.model import Rental as RentalModel 
from models.model import RentalStatus
from models.model import Staff as StaffModel 
from models.model import Cars as СarsModel 
from models.model import CarStatus
from models.model import Client as ClientModel 
from sqlalchemy.orm import Session


from core.security import *


class RentalController:
    def __init__(self, db: Session):
        self.db = db

    def get_all_rent(self):
        query = select(
            RentalModel.rental_id,
            RentalModel.client_id,
            RentalModel.car_id,
            RentalModel.staff_id,
            RentalModel.status_rent,
            RentalModel.start_time,
            RentalModel.end_time,
            RentalModel.total_hours,
            RentalModel.total_price
        ).order_by(RentalModel.staff_id)
        return paginate(self.db, query)
    
    def create_rent(self, rent_data: RentCreate, token):
        # try:
                
            check_client_id=self.db.execute(select(ClientModel.client_id).where(ClientModel.client_id == rent_data.client_id)).scalar_one_or_none()
            check_car_id=self.db.execute(select(СarsModel.car_id).where(СarsModel.car_id == rent_data.car_id)).scalar_one_or_none() 
            check_car_status= self.db.execute(select(СarsModel.is_available).where(СarsModel.car_id == rent_data.car_id)).scalar_one_or_none()
            if check_car_status != CarStatus.AVAILABLE:
                raise HTTPException(status_code=400, detail="Машина занята или находится в ремонте")
            # check_staff= подумать взять id или username сотрудника
            staff_username = decode_token(token)['sub']
            staff_id=self.db.execute(select(StaffModel.staff_id).where(StaffModel.username == staff_username)).scalar_one_or_none()

            if rent_data.start_time:
                start_time=rent_data.start_time
                if rent_data.start_time > rent_data.end_time:
                    timedelta = rent_data.start_time - rent_data.end_time
                    total_hours = timedelta.total_seconds()/3600
                    total_minutes = total_hours * 60
                    if total_hours < 1:
                        raise HTTPException(status_code=400, detail="время должно быть больше часа")
                else:
                    raise HTTPException(status_code=400, detail="время конца аренды должно быть больше чем время начала аренды")
            else:
                start_time = datetime.now(timezone.utc)
                timedelta = start_time - rent_data.end_time
                # можно запустить ассинхронный таймер с обратным отсчетом чтобы смотреть сколько осталось времени
                # или рассчитывать сколько осталось времени вычетая сейчас от даты конца аренды
                total_hours = timedelta.total_seconds()/3600
                total_minutes = total_hours * 60
            

            base_price_car = self.db.execute(select(СarsModel.daily_price).where(СarsModel.car_id == rent_data.car_id)).scalar_one_or_none()
            total_price = base_price_car // 24 * total_hours

            # возможно поменять  status_rent=rent_data.status_rent, на дефолтное active и убрать из схемы

            # статусы аренды     
            # ACTIVE = "active"
                # COMPLETED = "completed"
                # CANCELLED = "cancelled"

            Rent = RentalModel(
                    client_id=check_client_id,
                    car_id=check_car_id,
                    staff_id=staff_id,
                    status_rent=RentalStatus.ACTIVE,
                    start_time=start_time,
                    end_time=rent_data.end_time,
                    total_hours=total_minutes,
                    total_price=total_price
            )
            car_is_available = self.db.get(СarsModel, rent_data.car_id)
            car_is_available.is_available = CarStatus.RENTED

            self.db.add(Rent)
            self.db.commit()

            return Rent
        # except Exception as e:
        #     return {'error': f'Error: {e}'}
    
    def rent_cancelled(self, rent_id: int):
        rentalmodel=self.db.get(RentalModel, rent_id)
        if rentalmodel is None:
            raise HTTPException(
                status_code=404,
                detail="Аренда не найдена"
            )
        carmodel=self.db.get(СarsModel, rentalmodel.car_id)


        if rentalmodel.status_rent == RentalStatus.ACTIVE:
            carmodel.is_available = CarStatus.AVAILABLE
            rentalmodel.status_rent = RentalStatus.CANCELLED

        elif rentalmodel.status_rent == RentalStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail="Нельзя отменить завершенную аренду"
            )
        
        elif rentalmodel.status_rent == RentalStatus.CANCELLED:
            raise HTTPException(
                status_code=400,
                detail="Аренда уже отменена"
            )


        self.db.commit() 
        return {
        "message": "Аренда успешно отменена",
        "rental_id": rent_id,
        "status": rentalmodel.status_rent,
    }
    def rent_complete(self, rent_id: int):
        rentalmodel=self.db.get(RentalModel, rent_id)
        if rentalmodel is None:
            raise HTTPException(
                status_code=404,
                detail="Аренда не найдена"
            )
        carmodel=self.db.get(СarsModel, rentalmodel.car_id)


        if rentalmodel.status_rent == RentalStatus.ACTIVE:
            carmodel.is_available = CarStatus.AVAILABLE
            rentalmodel.status_rent = RentalStatus.COMPLETED

        elif rentalmodel.status_rent == RentalStatus.CANCELLED:
            raise HTTPException(
                status_code=400,
                detail="Нельзя завершить отменненую аренду"
            )
        
        elif rentalmodel.status_rent == RentalStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail="Аренда уже уже завершена или не была начата"
            )


        self.db.commit() 
        return {
        "message": "Аренда успешно завершена",
        "rental_id": rent_id,
        "status": rentalmodel.status_rent,
    }
    
    def clear_list_rent(self):
        all_id = self.db.execute(select(RentalModel.rental_id).where(RentalModel.status_rent != RentalStatus.ACTIVE)).scalars().all()
        self.db.execute(delete(RentalModel).where(RentalModel.status_rent != RentalStatus.ACTIVE))
        self.db.commit()
        return {
            "message": "Список завершенных или отменненых аренд очищен",
            "rental_id": f"Удаленные аренды id: {all_id} Всего: {len(all_id)}"
        }

    def get_rent_by_id(self, rent_id: int):
        rent = self.db.execute(select(RentalModel).where(RentalModel.rental_id == rent_id)).scalars().first()
        if rent:
            return rent
        else:
            raise HTTPException(status_code=404, detail="Аренда не найдена с таким id")

    def get_rent_by_client_id(self, client_id: int):
        rent = select(RentalModel).where(RentalModel.client_id == client_id).order_by(RentalModel.rental_id)
        result = self.db.execute(rent).scalars().all()
        if result:
            return paginate(self.db, rent)
        else:
            raise HTTPException(status_code=404, detail="Не найдено")

    def get_rent_by_car_id(self, car_id: int):
        rent = select(RentalModel).where(RentalModel.car_id == car_id).order_by(RentalModel.rental_id)
        result = self.db.execute(rent).scalars().all()
        if result:
            return paginate(self.db, rent)
        else:
            raise HTTPException(status_code=404, detail="Не найдено")


    def get_rent_by_staff_id(self, staff_id: int):
        rent = select(RentalModel).where(RentalModel.staff_id == staff_id).order_by(RentalModel.rental_id)
        result = self.db.execute(rent).scalars().all()
        if result:
            return paginate(self.db, rent)
        else:
            raise HTTPException(status_code=404, detail="Не найдено")

    def get_rent_by_status(self, status_rent: str):
        if status_rent in RentalStatus.__members__:
            rent = select(RentalModel).where(RentalModel.status_rent == status_rent).order_by(RentalModel.rental_id)
            result = self.db.execute(rent).scalars().all()
            if result:
                return paginate(self.db, rent)
            else:
                raise HTTPException(status_code=404, detail="Не найдено")
        else:
            raise HTTPException(status_code=404, detail="Не найдено")

