from fastapi import FastAPI, HTTPException
import uvicorn

from routes import camera, gas, motion, particle

from services.gas_service import get_gas
from services.motion_service import get_motion
from services.particle_service import get_particle
from services.camera_service import get_camera

from db.connection import create_tables, SessionLocal

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

@app.on_event("startup")
def startup_event():
    create_tables()
    print("API iniciada. Las tablas de base de datos están listas.")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)