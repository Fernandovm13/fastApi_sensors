import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime
from models.gas import GasSensor
from models.motion import MotionSensor
from models.particle import ParticleSensor
from models.camera import CameraCapture
from sqlalchemy import desc

from db.connection import create_tables, SessionLocal
from utils.time_utils import get_period_bounds_and_label
from routes import camera, gas, motion, particle

app = FastAPI(title="Sensor API Simple")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(gas.router)
app.include_router(motion.router)
app.include_router(particle.router)
app.include_router(camera.router)

# Endpoints para obtener el último dato de cada sensor
@app.get("/latest/gas")
def latest_gas():
    db = SessionLocal()
    try:
        latest = db.query(GasSensor).order_by(desc(GasSensor.timestamp)).first()
        if not latest:
            raise HTTPException(404, "No hay datos de gas")
        return latest
    finally:
        db.close()

@app.get("/latest/motion")
def latest_motion():
    db = SessionLocal()
    try:
        latest = db.query(MotionSensor).order_by(desc(MotionSensor.timestamp)).first()
        if not latest:
            raise HTTPException(404, "No hay datos de movimiento")
        return latest
    finally:
        db.close()

@app.get("/latest/particle")
def latest_particle():
    db = SessionLocal()
    try:
        latest = db.query(ParticleSensor).order_by(desc(ParticleSensor.timestamp)).first()
        if not latest:
            raise HTTPException(404, "No hay datos de partículas")
        return latest
    finally:
        db.close()

@app.get("/latest/camera")
def latest_camera():
    db = SessionLocal()
    try:
        latest = db.query(CameraCapture).order_by(desc(CameraCapture.timestamp)).first()
        if not latest:
            raise HTTPException(404, "No hay datos de cámara")
        return latest
    finally:
        db.close()

@app.on_event("startup")
def on_startup():
    # Crea las tablas si aún no existen
    create_tables()
    print("Tablas de base de datos listas")
    print(f"CORS configurado para permitir todos los orígenes")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)