from pydantic import BaseModel
from datetime import datetime

class GasDataBase(BaseModel):
    timestamp: datetime
    lpg: float
    co: float
    smoke: float
    system_id: int

class GasDataCreate(GasDataBase):
    pass

class GasDataRead(GasDataBase):
    id: str

    class Config:
        from_attributes = True
