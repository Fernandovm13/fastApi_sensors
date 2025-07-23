# routes/__init__.py

from .camera      import router as camera_router
from .gas         import router as gas_router
from .motion      import router as motion_router
from .particle    import router as particle_router
from .correlation import router as correlation_router

__all__ = [
    "camera_router",
    "gas_router",
    "motion_router",
    "particle_router",
    "correlation_router",
]
