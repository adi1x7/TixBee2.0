from .attractions import router as attractions_router
from .auth import router as auth_router
from .bookings import router as bookings_router
from .chat import router as chat_router
from .tickets import router as tickets_router
from .operations import router as operations_router
from .health import router as health_router

__all__ = ["attractions_router", "auth_router", "bookings_router", "chat_router", "tickets_router", "operations_router", "health_router"]
