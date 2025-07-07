from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from uuid import uuid4
from db.connection import Base

class CameraCapture(Base):
    __tablename__ = "camera_capture"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    timestamp = Column(DateTime, nullable=False)
    image_path = Column(String(255), nullable=False)
    motion_id = Column(
        String(36),
        ForeignKey("motion_sensors.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False
    )
    latency_ms = Column(Integer, nullable=False)
    system_id = Column(String(50), nullable=False)

    __table_args__ = (
        Index("idx_motion_id", "motion_id"),
    )
