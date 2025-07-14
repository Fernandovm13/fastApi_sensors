from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

from routes import camera, gas, motion, particle

from services.gas_service import get_gas
from services.motion_service import get_motion
from services.particle_service import get_particle
from services.camera_service import get_camera

from db.connection import create_tables, SessionLocal

app = FastAPI(title="Sensor API Simple")

# Configuración CORS robusta para React y AWS
def get_allowed_origins():
    """Obtiene los orígenes permitidos desde variables de entorno o valores por defecto"""
    # Para desarrollo local con React
    default_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    # Orígenes adicionales desde variables de entorno (para AWS/producción)
    env_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
    env_origins = [origin.strip() for origin in env_origins if origin.strip()]
    
    # Combinar orígenes por defecto con los de entorno
    all_origins = default_origins + env_origins
    
    return list(set(all_origins))  # Eliminar duplicados

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

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
    print(f"CORS configurado para: {get_allowed_origins()}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
