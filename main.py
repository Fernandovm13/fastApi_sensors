from fastapi import FastAPI, HTTPException
import uvicorn
import threading
import time

from routes import camera, gas, motion, particle

from simulators.camera_simulator import simulate_camera_once
from simulators.gas_simulator import simulate_gas_once
from simulators.motion_simulator import simulate_motion_once
from simulators.particle_simulator import simulate_particle_once

from services.gas_service import create_gas, get_gas
from services.motion_service import create_motion, get_motion
from services.particle_service import create_particle, get_particle
from services.camera_service import create_camera, get_camera

from schemas.gas import GasDataCreate
from schemas.motion import MotionDataCreate
from schemas.particle import ParticleDataCreate
from schemas.camera import CameraDataCreate

from db.connection import create_tables, SessionLocal
from models.motion import MotionSensor

app = FastAPI(title="Sensor API Simple")

app.include_router(gas.router)
app.include_router(motion.router)
app.include_router(particle.router)
app.include_router(camera.router)

@app.get("/latest/gas")
def latest_gas():
    db = SessionLocal()
    data = get_gas(db, start="2000-01-01", end="2100-01-01")
    db.close()
    if not data:
        raise HTTPException(404, "No hay datos de gas")
    return data[-1]

@app.get("/latest/motion")
def latest_motion():
    db = SessionLocal()
    data = get_motion(db, start="2000-01-01", end="2100-01-01")
    db.close()
    if not data:
        raise HTTPException(404, "No hay datos de movimiento")
    return data[-1]

@app.get("/latest/particle")
def latest_particle():
    db = SessionLocal()
    data = get_particle(db, start="2000-01-01", end="2100-01-01")
    db.close()
    if not data:
        raise HTTPException(404, "No hay datos de partículas")
    return data[-1]

@app.get("/latest/camera")
def latest_camera():
    db = SessionLocal()
    data = get_camera(db, start="2000-01-01", end="2100-01-01")
    db.close()
    if not data:
        raise HTTPException(404, "No hay datos de cámara")
    return data[-1]

def loop_simulator(name, simulate_fn, store_fn, schema_cls):

    while True:
        if name == "CAMERA":
            db = SessionLocal()
            last = (
                db.query(MotionSensor.id)
                  .order_by(MotionSensor.timestamp.desc())
                  .limit(1)
                  .one_or_none()
            )
            db.close()
            if last is None:
                time.sleep(1)
                continue
            motion_id = last[0]
            data = simulate_fn(motion_id)

        else:
            data = simulate_fn()

        db = SessionLocal()
        store_fn(db, schema_cls(**data.dict()))
        db.commit()
        db.close()

        print(f"[{name}]", data.json())
        time.sleep(2)

def start_simulators():
    simulators = [
        ("GAS",      simulate_gas_once,      create_gas,     GasDataCreate),
        ("MOTION",   simulate_motion_once,   create_motion,  MotionDataCreate),
        ("PARTICLE", simulate_particle_once, create_particle, ParticleDataCreate),
        ("CAMERA",   simulate_camera_once,   create_camera,  CameraDataCreate),
    ]
    for name, sim_fn, store_fn, schema in simulators:
        t = threading.Thread(
            target=loop_simulator,
            args=(name, sim_fn, store_fn, schema),
            daemon=True
        )
        t.start()

@app.on_event("startup")
def startup_event():
    create_tables()
    print("Iniciando simuladores...")
    start_simulators()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
