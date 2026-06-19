from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

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
    from app.core.redis_client import close_redis_client, get_redis_client, reset_redis_client

    get_redis_client()
    yield
    await close_redis_client()
    from app.core.dependencies import dispose_engine

    await dispose_engine()


settings = get_settings()

is_production = settings.ENVIRONMENT == "production"

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    lifespan=lifespan,
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
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

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


app.include_router(main_router)
