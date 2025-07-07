from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from schemas.gas import GasDataCreate, GasDataRead
from services.gas_service import create_gas, get_gas
from services.stats_utils import compute_stats
from db.connection import get_db

router = APIRouter(prefix="/gas", tags=["gas"])

@router.post("/", response_model=GasDataRead)
def add_gas(data: GasDataCreate, db: Session = Depends(get_db)):
    return create_gas(db, data)

@router.get("/all", response_model=list[GasDataRead])
def all_gas(db: Session = Depends(get_db)):
    start = datetime.min
    end   = datetime.max
    return get_gas(db, start, end)

@router.get("/statistics/{filter_type}")
def gas_stats(filter_type: str, db: Session = Depends(get_db)):
    today = datetime.today().date()
    if filter_type == 'today':
        start, end = today, today
    elif filter_type == 'last7':
        start, end = today - timedelta(days=6), today
    elif filter_type == 'month':
        start, end = today.replace(day=1), today
    else:
        raise HTTPException(400, "Invalid filter")
    records = get_gas(db, start, end)
    return compute_stats(records, ['lpg', 'co', 'smoke'])
