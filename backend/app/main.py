from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import attractions_router, auth_router, bookings_router, chat_router, health_router, operations_router, tickets_router
from app.services.seed import seed_catalog

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    seed_catalog()
    yield


app = FastAPI(title="TixBee API", version="1.0.0", docs_url="/docs", openapi_url=f"{settings.api_prefix}/openapi.json", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router)
app.include_router(attractions_router, prefix=settings.api_prefix)
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(bookings_router, prefix=settings.api_prefix)
app.include_router(chat_router, prefix=settings.api_prefix)
app.include_router(tickets_router, prefix=settings.api_prefix)
app.include_router(operations_router, prefix=settings.api_prefix)
