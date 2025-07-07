from sqlalchemy import Column, String, DECIMAL, Boolean, DateTime
from uuid import uuid4
from db.connection import Base

class MotionSensor(Base):
    __tablename__ = "motion_sensors"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    timestamp = Column(DateTime, nullable=False)
    motion_detected = Column(Boolean, nullable=False)
    intensity = Column(DECIMAL(6,2), nullable=False)
    system_id = Column(String(50), nullable=False)
