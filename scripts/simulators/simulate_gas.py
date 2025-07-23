import random, uuid
from datetime import datetime
from schemas.gas import GasDataCreate

def simulate_gas_once() -> GasDataCreate:
    return GasDataCreate(
        timestamp=datetime.now(),
        lpg=random.uniform(0, 1000),
        co=random.uniform(0, 50),
        smoke=random.uniform(0, 300),
        system_id="1"
    )

if __name__ == '__main__':
    from time import sleep
    while True:
        print(simulate_gas_once().json())
        sleep(2)
