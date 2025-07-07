from pydantic import BaseModel
from datetime import datetime

class MotionDataBase(BaseModel):
    timestamp: datetime
    motion_detected: bool
    intensity: float
    system_id: int

class MotionDataCreate(MotionDataBase):
    pass

class MotionDataRead(MotionDataBase):
    id: str

    class Config:
        from_attributes = True
