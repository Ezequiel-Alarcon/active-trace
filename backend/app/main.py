from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.database import create_engine, create_session_factory
from app.core.dependencies import get_engine, get_session_factory
from app.core.logging import configure_logging
from app.core.observability import init_telemetry, instrument_app
from app.api.v1.routers import health


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    init_telemetry()
    get_engine()
    get_session_factory()
    yield
    from app.core.database import _async_engine
    if _async_engine:
        await _async_engine.dispose()


settings = get_settings()
app = FastAPI(
    title="activia-trace",
    version="0.1.0",
    lifespan=lifespan,
)

instrument_app(app)

app.include_router(health.router)