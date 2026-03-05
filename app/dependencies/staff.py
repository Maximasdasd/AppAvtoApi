from db.db import get_db
from fastapi import Depends
from sqlalchemy.orm import Session
from controllers.staff import StaffController

def get_controllers_staff(db: Session = Depends(get_db)):
    return StaffController(db)