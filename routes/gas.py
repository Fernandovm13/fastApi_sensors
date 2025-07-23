# routes/gas.py

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from services.stats_utils import compute_stats
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
    start, end, label = get_period_bounds_and_label(filter_type)
    records = get_gas(db, start, end)
    stats = compute_stats(records, ['lpg', 'co', 'smoke'])
    return {'label': label, 'stats': stats}

@router.get("/report/{filter_type}")
def gas_full_report(filter_type: str, db: Session = Depends(get_db)):
    start, end, label = get_period_bounds_and_label(filter_type)
    records = get_gas(db, start, end)
    return compute_stats(records, ['lpg', 'co', 'smoke'])
