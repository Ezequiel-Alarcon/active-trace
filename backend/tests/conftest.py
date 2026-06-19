import asyncio
import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.database import Base


os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-chars-long")
os.environ.setdefault("ENCRYPTION_KEY", "12345678901234567890123456789012")
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/activia_trace_test"
)


_schema_applied = False


def _ensure_schema_sync() -> None:
    """Apply ORM-declared tables using a private engine + private loop.

    pytest-asyncio 1.4 + SQLAlchemy 2.0 async + asyncpg don't play well
    with session-scoped async fixtures: the session loop is torn down
    before function-scope teardown can complete. Running schema setup in
    a sync wrapper keeps the loop lifetime local to the call.
    """

    async def _go() -> None:
        import app.models.tenant  # noqa: F401  (register on Base.metadata)
        from app.models.mixins import TenantScopedMixin  # noqa: F401  (register on Base.metadata)
        import app.models.carrera  # noqa: F401
        import app.models.cohorte  # noqa: F401
        import app.models.materia  # noqa: F401
        import app.models.usuario  # noqa: F401
        import app.models.asignacion  # noqa: F401
        import app.models.programa_materia  # noqa: F401
        import app.models.fecha_academica  # noqa: F401
        import app.models.padron  # noqa: F401
        import app.audit.models  # noqa: F401  (register audit_log table)
        from app.auth import models  # noqa: F401  (register auth_* tables)
        from tests._fakes import models as _smoke  # noqa: F401  (register _smoke_tests)

        engine = create_async_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        finally:
            await engine.dispose()

    asyncio.run(_go())


def _session_is_all_no_db(request: pytest.FixtureRequest) -> bool:
    """True if every collected test in this session is marked `no_db`."""
    items = getattr(request.session.config, "_collected_items", None) or []
    if not items:
        return False
    return all(
        any(m.name == "no_db" for m in item.iter_markers()) for item in items
    )


@pytest.fixture(scope="session", autouse=True)
def _apply_schema_once(request: pytest.FixtureRequest) -> None:
    """Create all ORM-declared tables once per test session.

    C-02 brings the first models; we don't have a full Alembic pipeline yet,
    so tests share `Base.metadata.create_all` to set up the schema. Migration
    tests (`test_alembic_migration_001`) apply and revert Alembic explicitly
    on a different schema path.

    If every collected test in this session carries `@pytest.mark.no_db`,
    skip schema setup because no test needs DB.
    """
    if _session_is_all_no_db(request):
        return
    global _schema_applied
    if not _schema_applied:
        _ensure_schema_sync()
        _schema_applied = True


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Stash the collected items on the session so the session-scope autouse
    fixture can inspect them later."""
    config._collected_items = items  # type: ignore[attr-defined]


@pytest.fixture(scope="session", autouse=True)
def _ensure_auth_models_registered() -> None:
    """Import the auth models so `Base.metadata.create_all` (and Alembic
    autogenerate) can see them. Idempotent and free of side effects."""
    try:
        from app.auth import models  # noqa: F401  (registers auth_* tables)
    except ImportError:
        pass


@pytest.fixture
def set_tenant_context():
    """Factory fixture: returns a callable that sets the tenant context
    for the duration of a block. Mirrors `tenant_scope` but as a test fixture."""
    from app.core.tenancy import TenantContext, set_tenant_context

    def _set(tenant_id):
        token = set_tenant_context(TenantContext(tenant_id=tenant_id))
        return token

    return _set


@pytest.fixture
def mint_test_jwt():
    """Factory fixture: returns a callable that mints an access JWT for the
    given (user_id, tenant_id, session_id). Used by tests that need to
    authenticate HTTP requests after the C-03 header removal.
    """
    from uuid import UUID, uuid4

    from app.core.security.jwt import encode_access_token

    def _mint(user_id: UUID | None = None, tenant_id: UUID | None = None, session_id: UUID | None = None) -> str:
        return encode_access_token(
            user_id=user_id or uuid4(),
            tenant_id=tenant_id or uuid4(),
            session_id=session_id or uuid4(),
            jti=uuid4(),
        )

    return _mint


def _make_session_factory_per_test() -> tuple[AsyncEngine, async_sessionmaker]:
    """Build a per-test session factory bound to a fresh engine + loop.

    Caching the engine across tests on pytest-asyncio 1.4 leaks the
    previous event loop into the next test ("Event loop is closed" from
    asyncpg). So we build a fresh engine per test and dispose it on
    teardown.

    # TODO: (HACK) Crear un engine por test es costoso (overhead de conexión).
    # Es necesario porque pytest-asyncio 1.4 usa function-scoped event loops y
    # asyncpg vincula sus conexiones al loop en que se crearon. Reutilizar el
    # engine causaría "Event loop is closed" en el segundo test. Migrar a
    # anyio o a session-scoped loops eliminaría esta necesidad.
    """
    engine = create_async_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
    return engine, async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """A session per test, with a per-test engine to avoid loop leakage."""
    engine, factory = _make_session_factory_per_test()
    try:
        async with factory() as session:
            yield session
            try:
                await session.rollback()
            except Exception:
                pass
    finally:
        await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    engine = create_async_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def _reset_app_engine_async():
    """Reset FastAPI's cached engine for tests that use AsyncClient.

    pytest-asyncio 1.4 creates a new event loop per test function. The
    FastAPI app caches a single AsyncEngine in app.core.dependencies. If
    that engine was created in a previous test's loop (now closed), the next
    HTTP request will hit 'RuntimeError: Event loop is closed'.

    Import this fixture in test files that use AsyncClient (NOT autouse —
    only tests that actually hit the HTTP layer need it).

    # TODO: (HACK) El engine de FastAPI (app.core.dependencies._async_engine)
    # es un singleton que se inicializa una sola vez. pytest-asyncio 1.4 crea
    # un event loop nuevo por cada función de test, por lo que el engine del
    # test anterior queda ligado a un loop cerrado y rompe la siguiente petición
    # HTTP con "RuntimeError: Event loop is closed". Este fixture fuerza el
    # descarte y recreación del engine antes y después de cada test que use
    # AsyncClient. La solución definitiva requiere migrar a session-scoped loops
    # o usar anyio, pero implica cambios en toda la suite.
    """
    from app.core import dependencies as _app_deps
    old_engine = _app_deps._async_engine
    _app_deps._async_engine = None
    _app_deps._async_session_factory = None
    if old_engine is not None:
        try:
            await old_engine.dispose()
        except Exception:
            pass
    yield
    old_engine = _app_deps._async_engine
    _app_deps._async_engine = None
    _app_deps._async_session_factory = None
    if old_engine is not None:
        try:
            await old_engine.dispose()
        except Exception:
            pass
