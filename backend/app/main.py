from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.dependencies import get_engine, get_session_factory
from app.core.logging import configure_logging
from app.core.observability import init_telemetry, instrument_app
from app.api.v1.main_router import main_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    init_telemetry()
    get_engine()
    get_session_factory()
    yield
    from app.core.dependencies import dispose_engine

    await dispose_engine()


settings = get_settings()
app = FastAPI(
    title="activia-trace",
    version="0.1.0",
    lifespan=lifespan,
)

# Instrument OpenTelemetry BEFORE adding middleware
# This ensures CORS (and other middleware) wrap OTel, preventing preflight crashes
instrument_app(app)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(main_router)
