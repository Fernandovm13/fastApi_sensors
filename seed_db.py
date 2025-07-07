from datetime import datetime, timedelta
from uuid import uuid4
from db.connection import SessionLocal
from services.gas_service      import create_gas
from services.motion_service   import create_motion
from services.particle_service import create_particle
from services.camera_service   import create_camera
from schemas.gas      import GasDataCreate
from schemas.motion   import MotionDataCreate
from schemas.particle import ParticleDataCreate
from schemas.camera   import CameraDataCreate

def make_timestamps():
    now = datetime.now()
    return {
        "today":  now,
        "3days":  now - timedelta(days=3),
        "10days": now - timedelta(days=10),
        "1month": now - timedelta(days=30),
    }

def seed_gas(db, ts):
    reading = GasDataCreate(
        timestamp=ts,
        lpg=500.0 + ts.day,
        co=20.0  + ts.day/2,
        smoke=100.0 + ts.day*3,
        system_id="1"
    )
    create_gas(db, reading)

def seed_motion(db, ts):
    reading = MotionDataCreate(
        timestamp=ts,
        motion_detected=(ts.day % 2 == 0),
        intensity=float((ts.day % 10) + 1),
        system_id="1"
    )
    obj = create_motion(db, reading)
    return obj.id  

def seed_particle(db, ts):
    reading = ParticleDataCreate(
        timestamp=ts,
        pm1_0=float(ts.day + 1),
        pm2_5=float(ts.day * 2),
        pm10=float(ts.day * 3),
        system_id="1"
    )
    create_particle(db, reading)

def seed_camera(db, ts, motion_id):
    reading = CameraDataCreate(
        timestamp=ts,
        image_path=f"/uploads/img_{uuid4().hex}.jpg",
        motion_id=motion_id,       
        latency_ms=100 + ts.day,
        system_id="1"
    )
    create_camera(db, reading)

def main():
    timestamps = make_timestamps()
    db = SessionLocal()
    try:
        for label, ts in timestamps.items():
            print(f"Seeding for {label} @ {ts}")
            seed_gas(db, ts)
            seed_particle(db, ts)
            mid = seed_motion(db, ts)
            seed_camera(db, ts, mid)
        print("Seeding complete")
    except Exception as e:
        print("Error during seeding:", e)
    finally:
        db.close()

if __name__ == "__main__":
    main()
