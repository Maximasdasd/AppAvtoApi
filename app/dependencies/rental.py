from db.db import get_db
from fastapi import Depends
from sqlalchemy.orm import Session
from controllers.rental import RentalController

def get_controllers_rental(db: Session = Depends(get_db)):
    return RentalController(db)