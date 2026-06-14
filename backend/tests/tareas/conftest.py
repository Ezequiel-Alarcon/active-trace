from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest_asyncio
import sqlalchemy
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.security.hashing import hash_email_for_search
from app.core.security.passwords import hash_password
from app.models.base import Base
from app.models.tenant import Tenant, TenantEstado
from app.rbac.constants import GLOBAL_TENANT_ID
from app.rbac.models import Permiso, Rol, RolPermiso

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/activia_trace_test"
)

TAREAS_GESTIONAR_ID = UUID("00000000-0000-0000-0001-c00000000003")


@pytest_asyncio.fixture
async def db_setup():
    import app.models.tarea  # noqa: F401  — register tarea models on Base.metadata
    from app.models import tenant  # noqa: F401
    from app.models import carrera, cohorte, materia  # noqa: F401
    from app.rbac import models as _rbac_models  # noqa: F401
    from app.auth import models as _auth_models  # noqa: F401

    engine = create_async_engine(os.environ["DATABASE_URL"])
    async with engine.begin() as conn:
        await conn.execute(sqlalchemy.text("DROP TABLE IF EXISTS _smoke_tests CASCADE"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    yield factory
    await engine.dispose()


async def _seed_rbac(session, *, include_tareas=True) -> dict[str, UUID]:
    gid = GLOBAL_TENANT_ID

    t = await session.get(Tenant, gid)
    if t is None:
        t = Tenant(id=gid, codigo="GLOBAL", nombre="Global System Tenant", estado=TenantEstado.ACTIVO)
        session.add(t)
        await session.flush()

    role_ids = {
        "ALUMNO": UUID("00000000-0000-0000-0000-a00000000002"),
        "TUTOR": UUID("00000000-0000-0000-0000-a00000000003"),
        "COORDINADOR": UUID("00000000-0000-0000-0000-a00000000004"),
        "NEXO": UUID("00000000-0000-0000-0000-a00000000005"),
        "ADMIN": UUID("00000000-0000-0000-0000-a00000000006"),
        "FINANZAS": UUID("00000000-0000-0000-0000-a00000000007"),
        "PROFESOR": UUID("00000000-0000-0000-0000-a00000000008"),
    }

    for name, rid in role_ids.items():
        existing = await session.get(Rol, rid)
        if existing is None:
            session.add(Rol(id=rid, tenant_id=gid, nombre=name, descripcion=name))

    if include_tareas:
        existing = await session.get(Permiso, TAREAS_GESTIONAR_ID)
        if existing is None:
            session.add(Permiso(id=TAREAS_GESTIONAR_ID, tenant_id=gid, modulo="tareas", accion="gestionar"))

    await session.flush()

    if include_tareas:
        for rol_name in ("PROFESOR", "COORDINADOR", "ADMIN"):
            from sqlalchemy import select
            existing = await session.execute(
                select(RolPermiso).where(
                    RolPermiso.tenant_id == gid,
                    RolPermiso.rol_id == role_ids[rol_name],
                    RolPermiso.permiso_id == TAREAS_GESTIONAR_ID,
                )
            )
            if existing.scalar_one_or_none() is None:
                session.add(RolPermiso(tenant_id=gid, rol_id=role_ids[rol_name], permiso_id=TAREAS_GESTIONAR_ID))

    await session.flush()
    return role_ids


async def _create_tenant(session) -> Tenant:
    t = Tenant(codigo="TENANT-TEST", nombre="Test Tenant", estado=TenantEstado.ACTIVO)
    session.add(t)
    await session.flush()
    return t


async def _create_user_and_session(
    session, tenant_id: UUID, *, rol_id: UUID | None = None,
) -> tuple[UUID, UUID, UUID]:
    from app.auth.models import AuthSession, AuthUser

    user_id = uuid4()
    u = AuthUser(
        id=user_id,
        tenant_id=tenant_id,
        email_enc=f"enc:user_{user_id.hex[:8]}@test.com",
        email_hash=hash_email_for_search(f"user_{user_id.hex[:8]}@test.com", tenant_id),
        password_hash=hash_password("Pa55word!"),
    )
    session.add(u)
    await session.flush()

    now = datetime.now(timezone.utc)
    session_id = uuid4()
    s = AuthSession(
        tenant_id=tenant_id,
        user_id=user_id,
        refresh_token_hash="hash",
        jti=uuid4(),
        issued_at=now,
        expires_at=now + timedelta(days=1),
        id=session_id,
    )
    session.add(s)
    await session.flush()

    user_rol_id = rol_id or UUID("00000000-0000-0000-0000-a00000000006")
    from app.models.asignacion import Asignacion, ContextoTipo
    asig = Asignacion(
        tenant_id=tenant_id,
        usuario_id=user_id,
        rol_id=user_rol_id,
        contexto_tipo=ContextoTipo.GLOBAL,
        desde=datetime.now(timezone.utc).date(),
    )
    session.add(asig)
    await session.flush()

    return user_id, tenant_id, session_id
