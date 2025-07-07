from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from schemas.particle import ParticleDataCreate, ParticleDataRead
from services.particle_service import create_particle, get_particle
from services.stats_utils import compute_stats
from db.connection import get_db

router = APIRouter(prefix="/particle", tags=["particle"])

@router.post("/", response_model=ParticleDataRead)
def add_particle(data: ParticleDataCreate, db: Session = Depends(get_db)):
    return create_particle(db, data)

@router.get("/all", response_model=list[ParticleDataRead])
def all_particles(db: Session = Depends(get_db)):
    start = datetime.min
    end   = datetime.max
    return get_particle(db, start, end)

@router.get("/statistics/{filter_type}")
def particle_stats(filter_type: str, db: Session = Depends(get_db)):
    today = datetime.today().date()
    if filter_type == 'today':
        start, end = today, today
    elif filter_type == 'last7':
        start, end = today - timedelta(days=6), today
    elif filter_type == 'month':
        start, end = today.replace(day=1), today
    else:
        raise HTTPException(400, "Invalid filter")
    records = get_particle(db, start, end)
    return compute_stats(records, ['pm1_0', 'pm2_5', 'pm10'])
