from typing import List
from sqlalchemy.orm import Session
from models.motion import MotionSensor
from schemas.motion import MotionDataCreate  

def create_motion(db: Session, data: MotionDataCreate) -> MotionSensor:
    obj = MotionSensor(**data.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def get_motion(db: Session, start, end) -> List[MotionSensor]:
    return (
        db.query(MotionSensor)
          .filter(MotionSensor.timestamp >= start, MotionSensor.timestamp <= end)
          .all()
    )
