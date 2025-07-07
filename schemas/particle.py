from pydantic import BaseModel
from datetime import datetime

class ParticleDataBase(BaseModel):
    timestamp: datetime
    pm1_0: float
    pm2_5: float
    pm10: float
    system_id: int

class ParticleDataCreate(ParticleDataBase):
    pass

class ParticleDataRead(ParticleDataBase):
    id: str

    class Config:
        from_attributes = True
