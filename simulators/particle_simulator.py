import random, uuid
from datetime import datetime
from schemas.particle import ParticleDataCreate

def simulate_particle_once() -> ParticleDataCreate:
    return ParticleDataCreate(
        timestamp=datetime.now(),
        pm1_0=random.uniform(0, 50),
        pm2_5=random.uniform(0, 100),
        pm10=random.uniform(0, 200),
        system_id="1"
    )

if __name__ == '__main__':
    from time import sleep
    while True:
        print(simulate_particle_once().json())
        sleep(2)
