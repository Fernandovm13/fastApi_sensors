from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from schemas.motion import MotionDataCreate, MotionDataRead
from services.motion_service import create_motion, get_motion
from services.stats_utils import compute_stats
from db.connection import get_db

router = APIRouter(prefix="/motion", tags=["motion"])

@router.post("/", response_model=MotionDataRead)
def add_motion(data: MotionDataCreate, db: Session = Depends(get_db)):
    return create_motion(db, data)

@router.get("/all", response_model=list[MotionDataRead])
def all_motion(db: Session = Depends(get_db)):
    start = datetime.min
    end   = datetime.max
    return get_motion(db, start, end)

@router.get("/statistics/{filter_type}")
def motion_stats(filter_type: str, db: Session = Depends(get_db)):
    today = datetime.today().date()
    if filter_type == 'today':
        start, end = today, today
    elif filter_type == 'last7':
        start, end = today - timedelta(days=6), today
    elif filter_type == 'month':
        start, end = today.replace(day=1), today
    else:
        raise HTTPException(400, "Invalid filter")
    records = get_motion(db, start, end)
    return compute_stats(records, ['intensity'])
