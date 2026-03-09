from fastapi import HTTPException, Request
from sqlalchemy import select, delete, exists
from fastapi_pagination.ext.sqlalchemy import paginate
from schemas.staff import StaffResponsePublic, StaffCreate
from models.model import Staff as StaffModel 
from models.model import RefreshToken as RefreshTokenModel
from sqlalchemy.orm import Session


from core.security import get_password_hash, verify_password, create_access_token, create_refresh_token, decode_token

class StaffController:
    def __init__(self, db: Session):
        self.db = db



    def get_all_staff(self):
        query = select(
            StaffModel.staff_id,
            StaffModel.username,
            StaffModel.full_name,
            StaffModel.email,
            StaffModel.phone,
            StaffModel.position
        ).order_by(StaffModel.staff_id)
        return paginate(self.db, query)



    def get_staff_by_id(self, staff_id: int) -> StaffResponsePublic:
        staff = self.db.get(StaffModel, staff_id)
        if staff:
            return staff
        else:
            raise HTTPException(status_code=404, detail="Сотрудник не найден")
        


    def create_staff(self, staff_data: StaffCreate):
        check_username = self.db.execute(select(StaffModel).where(StaffModel.username == staff_data.username)).scalar_one_or_none()
            
        if check_username:
            raise HTTPException(status_code=409, detail="Сотрудник с таким логином уже существует")
        
        check_email = self.db.execute(select(StaffModel).where(StaffModel.email == staff_data.email)).scalar_one_or_none()
        
        if check_email:
            raise HTTPException(status_code=409, detail="Сотрудник с таким E-mail уже существует")
        
        check_phone = self.db.execute(select(StaffModel).where(StaffModel.phone == staff_data.phone)).scalar_one_or_none()
        
        if check_phone:
            raise HTTPException(status_code=409, detail="Сотрудник с таким телефоном уже существует")

        password_hashed = get_password_hash(staff_data.password)
        
        staff = StaffModel(
                username=staff_data.username,
                full_name=staff_data.full_name,
                password_hashed=password_hashed,
                email=staff_data.email,
                phone=staff_data.phone,
                position=staff_data.position
        )
            
        self.db.add(staff)
        self.db.commit()
        return staff
    


    def delete_staff(self, staff_id: int):
        staff = self.db.get(StaffModel, staff_id)
        if staff:
            if staff.staff_id == 1 or staff.position == "admin":
                raise HTTPException(status_code=403, detail="Операция запрещена: нельзя удалить администратора")
            else:
                self.db.delete(staff)
                self.db.commit()
                return {"message": "Сотрудник удалён"}
        else:
            raise HTTPException(status_code=404, detail="Сотрудник не найден")
        


    def add_refresh_token_in_db(self, refresh_token, username):
        addtokeninbd = RefreshTokenModel(
                token=refresh_token,
                staff_id=self.db.execute(select(StaffModel.staff_id).where(StaffModel.username == username)).scalar_one_or_none(),
                expires_at='30days'
        )

        self.db.add(addtokeninbd)
        self.db.commit()



    def login_staff(self, username: str, password: str):
        roles = self.db.execute(select(StaffModel.position).where(StaffModel.username == username)).scalar_one_or_none()
        if not roles:
            raise HTTPException(
                status_code=404,
                detail="Пользователь не найден"
            )

        if verify_password(password, self.db.execute(select(StaffModel.password_hashed).where(StaffModel.username == username)).scalar_one_or_none()):
            access_token=create_access_token({'sub': username}, [roles])
            refresh_token = create_refresh_token({'sub': username})

            self.add_refresh_token_in_db(refresh_token, username)

            return {
                "refresh_token": refresh_token,
                "access_token": access_token,
                "token_type": "bearer"
            }
        else:
            raise HTTPException(status_code=404, detail="Неверный пароль")



    def refresh_token_revoke(self, token):
        result = self.db.execute(select(RefreshTokenModel).where(RefreshTokenModel.token == token)).scalar_one_or_none()

        if not result:
            raise HTTPException(status_code=404, detail="Токен не найден")
        
        if result.is_revoked is True:
            raise HTTPException(status_code=400, detail="Токен уже отменён")

        result.is_revoked = True
        self.db.commit()

        return {"token": "cancelled"}



    def refresh_token(self, token):
        token_revoke = self.db.execute(select(RefreshTokenModel.is_revoked).where(RefreshTokenModel.token == token)).scalar_one_or_none()

        def get_roles_from_db(sub:str):
            return self.db.execute(select(StaffModel.position).where(StaffModel.username == sub)).scalar_one_or_none()
        
        if token_revoke == False:

            payload = decode_token(token)

            if payload['type'] == 'refresh':

                access_token = create_access_token({'sub': payload["sub"]}, get_roles_from_db(payload["sub"]))
                refresh_token_rotate = create_refresh_token({'sub': payload["sub"]})

                self.refresh_token_revoke(token)
                self.add_refresh_token_in_db(refresh_token_rotate, payload["sub"])

                return {'access_token': access_token,
                        "refresh_token": refresh_token_rotate}
            else:
                return {'token_type': 'notrefresh'}
            
        elif token_revoke == True:
            raise HTTPException(400, detail="Токен отменен")
        
        else:
            raise HTTPException(404, detail="Токен не найден")


    def info_me(self, token):
        if token:
            return decode_token(token)
        else:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        

    