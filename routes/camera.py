from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from schemas.camera import CameraDataCreate, CameraDataRead
from services.camera_service import create_camera, get_camera
from services.stats_utils import compute_stats
from db.connection import get_db

router = APIRouter(prefix="/camera", tags=["camera"])

@router.post("/", response_model=CameraDataRead)
def add_capture(data: CameraDataCreate, db: Session = Depends(get_db)):
    return create_camera(db, data)

@router.get("/all", response_model=list[CameraDataRead])
def all_camera(db: Session = Depends(get_db)):
    start = datetime.min
    end   = datetime.max
    return get_camera(db, start, end)

@router.get("/statistics/{filter_type}")
def camera_stats(filter_type: str, db: Session = Depends(get_db)):
    today = datetime.today().date()
    if filter_type == 'today':
        start, end = today, today
    elif filter_type == 'last7':
        start, end = today - timedelta(days=6), today
    elif filter_type == 'month':
        start, end = today.replace(day=1), today
    else:
        raise HTTPException(400, "Invalid filter")
    records = get_camera(db, start, end)
    return compute_stats(records, ['latency_ms'])
