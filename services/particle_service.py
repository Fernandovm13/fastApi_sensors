from typing import List
from sqlalchemy.orm import Session
from models.particle import ParticleSensor
from schemas.particle import ParticleDataCreate   

def create_particle(db: Session, data: ParticleDataCreate) -> ParticleSensor:
    obj = ParticleSensor(**data.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def get_particle(db: Session, start, end) -> List[ParticleSensor]:
    return (
        db.query(ParticleSensor)
          .filter(ParticleSensor.timestamp >= start, ParticleSensor.timestamp <= end)
          .all()
    )
