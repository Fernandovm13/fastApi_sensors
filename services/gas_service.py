from typing import List
from sqlalchemy.orm import Session
from models.gas import GasSensor
from schemas.gas import GasDataCreate   

def create_gas(db: Session, data: GasDataCreate) -> GasSensor:
    obj = GasSensor(**data.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def get_gas(db: Session, start, end) -> List[GasSensor]:
    return (
        db.query(GasSensor)
          .filter(GasSensor.timestamp >= start, GasSensor.timestamp <= end)
          .all()
    )
