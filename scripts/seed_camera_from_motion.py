from uuid import uuid4
from db.connection import SessionLocal
from services.camera_service import create_camera
from schemas.camera import CameraDataCreate

# Importa tu modelo ORM correctamente
from models.motion import MotionSensor

def seed_camera_from_motion(db, limit=500):
    # 1) Obtener los primeros `limit` registros de MotionSensor
    motions = (
        db.query(MotionSensor.id, MotionSensor.timestamp)
          .order_by(MotionSensor.timestamp)  # o el criterio que prefieras
          .limit(limit)
          .all()
    )

    # 2) Para cada registro, crear un CameraDataCreate y llamar a create_camera
    for motion_id, ts in motions:
        reading = CameraDataCreate(
            timestamp=ts,
            image_path=f"/uploads/img_{uuid4().hex}.jpg",
            motion_id=motion_id,
            latency_ms=100 + ts.day,
            system_id="1"
        )
        create_camera(db, reading)
        print(f"→ Cámara inyectada para motion {motion_id} @ {ts}")

def main():
    db = SessionLocal()
    try:
        print("Iniciando inyección de cámaras basadas en motion existentes...")
        seed_camera_from_motion(db, limit=500)
        print("¡Inyección de camera completa!")
    except Exception as e:
        print("Error durante la inyección de camera:", e)
    finally:
        db.close()

if __name__ == "__main__":
    main()
