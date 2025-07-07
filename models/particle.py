from sqlalchemy import Column, String, DECIMAL, DateTime
from uuid import uuid4
from db.connection import Base

class ParticleSensor(Base):
    __tablename__ = "particle_sensor"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    timestamp = Column(DateTime, nullable=False)
    pm1_0 = Column(DECIMAL(8,2), nullable=False)
    pm2_5 = Column(DECIMAL(8,2), nullable=False)
    pm10  = Column(DECIMAL(8,2), nullable=False)
    system_id = Column(String(50), nullable=False)
