from typing import List
from sqlalchemy.orm import Session
from models.camera import CameraCapture
from schemas.camera import CameraDataCreate

def create_camera(db: Session, data: CameraDataCreate) -> CameraCapture:
    obj = CameraCapture(**data.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def get_camera(db: Session, start, end) -> List[CameraCapture]:
    return (
        db.query(CameraCapture)
          .filter(CameraCapture.timestamp >= start, CameraCapture.timestamp <= end)
          .all()
    )
