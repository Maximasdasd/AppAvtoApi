from db.db import get_db
from fastapi import Depends
from controllers.car import CarController
from sqlalchemy.orm import Session

def get_controllers(db: Session = Depends(get_db)) -> CarController:
    return CarController(db)


