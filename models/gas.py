from sqlalchemy import Column, String, DECIMAL, DateTime
from uuid import uuid4
from db.connection import Base

class GasSensor(Base):
    __tablename__ = "gas_sensor"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    timestamp = Column(DateTime, nullable=False)
    lpg   = Column(DECIMAL(6,2), nullable=False)
    co    = Column(DECIMAL(6,2), nullable=False)
    smoke = Column(DECIMAL(6,2), nullable=False)
    system_id = Column(String(50), nullable=False)
