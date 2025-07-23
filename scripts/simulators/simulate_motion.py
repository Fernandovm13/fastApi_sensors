import random, uuid
from datetime import datetime
from schemas.motion import MotionDataCreate

def simulate_motion_once() -> MotionDataCreate:
    return MotionDataCreate(
        timestamp=datetime.now(),
        motion_detected=random.choice([True, False]),
        intensity=random.uniform(0, 10),
        system_id="1"
    )

if __name__ == '__main__':
    from time import sleep
    while True:
        print(simulate_motion_once().json())
        sleep(2)
