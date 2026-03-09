# controller/client.py
from fastapi import HTTPException
from sqlalchemy import select, delete, exists
from fastapi_pagination.ext.sqlalchemy import paginate
from schemas.client import ClientResponse, ClientCreate
from models.model import Client as ClientModel 
from sqlalchemy.orm import Session


class ClientController:
    def __init__(self, db: Session):
        self.db = db


    def get_client(self):
        """Функция для вывода всех клиентов с пагинацией"""
        query = select(ClientModel).order_by(ClientModel.client_id)
        return paginate(self.db, query)


    def get_client_by_id(self, client_id: int) -> ClientResponse:
        client = self.db.get(ClientModel, client_id)
        if client:
            return client
        else:
            raise HTTPException(status_code=404, detail="Клиент не найден")


    def create_client(self, client_data: ClientCreate):
        """функция для создании клиента"""
        check_driver_license = self.db.execute(select(ClientModel).where(ClientModel.driver_license == client_data.driver_license)).scalar_one_or_none()
            
        if check_driver_license:
            raise HTTPException(status_code=409, detail="Такой водитель уже существует")
        
        check_passport = self.db.execute(select(ClientModel).where(ClientModel.passport == client_data.passport)).scalar_one_or_none()
        
        if check_passport:
            raise HTTPException(status_code=409, detail="Такой паспорт уже существует")
        
        client = ClientModel(
                full_name=client_data.full_name,
                driver_license=client_data.driver_license,
                passport=client_data.passport,
                address=client_data.address
        )
            
        self.db.add(client)
        self.db.commit()
        return client

    def refresh_client(self, client_new_data: ClientCreate, client_id:int):
        check_driver_license = self.db.execute(select(ClientModel).where(ClientModel.driver_license == client_new_data.driver_license)).scalar_one_or_none()
            
        if check_driver_license:
            raise HTTPException(status_code=409, detail="Такой водитель уже существует")
        
        check_passport = self.db.execute(select(ClientModel).where(ClientModel.passport == client_new_data.passport)).scalar_one_or_none()
        
        if check_passport:
            raise HTTPException(status_code=409, detail="Такой паспорт уже существует")

        client = self.db.get(ClientModel, client_id)
        if client:
            if client_new_data.full_name:
                client.full_name = client_new_data.full_name
            if client_new_data.driver_license:
                client.driver_license = client_new_data.driver_license
            if client_new_data.passport:
                client.passport = client_new_data.passport
            if client_new_data.address:
                client.address = client_new_data.address
                self.db.commit()
                return client
        else:
            raise HTTPException(status_code=404, detail="Клиент не найден")
        

    def delete_all_clients(self):
        has_clients = self.db.execute(
            select(exists().select_from(ClientModel))
        ).scalar_one()
        if not has_clients:
            raise HTTPException(404, "Клиенты не найдены")
        else:
            self.db.execute(delete(ClientModel))
            self.db.commit()
            return {"message": "Все клиенты удалены"}
