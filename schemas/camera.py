from pydantic import BaseModel
from datetime import datetime

class CameraDataBase(BaseModel):
    timestamp: datetime
    image_path: str
    motion_id: str
    latency_ms: int
    system_id: int

class CameraDataCreate(CameraDataBase):
    pass

class CameraDataRead(CameraDataBase):
    id: str

    class Config:
        from_attributes = True
