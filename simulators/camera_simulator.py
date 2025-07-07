import random, uuid
from datetime import datetime
from schemas.camera import CameraDataCreate

def simulate_camera_once(motion_id: str) -> CameraDataCreate:
    return CameraDataCreate(
        timestamp    = datetime.now(),
        image_path   = f"/uploads/img_{uuid.uuid4().hex}.jpg",
        motion_id    = motion_id,
        latency_ms   = random.randint(50, 300),
        system_id    = "1"
    )

if __name__ == '__main__':
    mid = "00000000-0000-0000-0000-000000000000"
    from time import sleep
    while True:
        print(simulate_camera_once(mid).json())
        sleep(2)
