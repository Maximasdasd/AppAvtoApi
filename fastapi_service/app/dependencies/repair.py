from db.db import get_db
from fastapi import Depends
from sqlalchemy.orm import Session
from controllers.repair import RepairController

def get_controllers_repair(db: Session = Depends(get_db)):
    return RepairController(db)