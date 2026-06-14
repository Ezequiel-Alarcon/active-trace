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
from app.models.usuario import Usuario
from app.repositories.usuarios import encrypt_usuario_fields

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/activia_trace_test"
)


@pytest_asyncio.fixture
async def db_setup():
    import app.models.mensaje_interno  # noqa: F401
    from app.models import tenant  # noqa: F401
    from app.auth import models as _auth_models  # noqa: F401
    from app.rbac import models as _rbac_models  # noqa: F401

    engine = create_async_engine(os.environ["DATABASE_URL"])
    async with engine.begin() as conn:
        await conn.execute(sqlalchemy.text("DROP TABLE IF EXISTS _smoke_tests CASCADE"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    yield factory
    await engine.dispose()


async def _create_tenant(session) -> Tenant:
    t = Tenant(codigo="TENANT-PERFIL", nombre="Perfil Test Tenant", estado=TenantEstado.ACTIVO)
    session.add(t)
    await session.flush()
    return t


async def _create_usuario(
    session, tenant_id: UUID, *, extra: dict | None = None
) -> Usuario:
    data = {
        "nombre": "Juan",
        "apellidos": "Pérez",
        "email": f"juan.perez.{uuid4().hex[:8]}@test.com",
        "dni": "12345678",
        "cuil": "20-12345678-9",
        "cbu": "0000003100012345678901",
        "alias_cbu": None,
        "banco": "Banco Test",
        "regional": "CABA",
        "legajo": "LEG-001",
        "legajo_profesional": None,
        "fecha_nacimiento": None,
        "genero": None,
        "observaciones": None,
    }
    if extra:
        data.update(extra)

    if "alias_cbu" in data and data["alias_cbu"] is None:
        del data["alias_cbu"]
        encrypted = encrypt_usuario_fields(data, tenant_id)
        encrypted["alias_cbu_enc"] = None
    else:
        encrypted = encrypt_usuario_fields(data, tenant_id)
    encrypted["tenant_id"] = tenant_id
    u = Usuario(**encrypted)
    session.add(u)
    await session.flush()
    return u


async def _create_auth_user_and_session(
    session, tenant_id: UUID, usuario_id: UUID
) -> tuple[UUID, UUID]:
    from app.auth.models import AuthSession, AuthUser

    au = AuthUser(
        id=usuario_id,
        tenant_id=tenant_id,
        email_enc=f"enc:user_{usuario_id.hex[:8]}@test.com",
        email_hash=hash_email_for_search(f"user_{usuario_id.hex[:8]}@test.com", tenant_id),
        password_hash=hash_password("Pa55word!"),
    )
    session.add(au)
    await session.flush()

    now = datetime.now(timezone.utc)
    session_id = uuid4()
    s = AuthSession(
        tenant_id=tenant_id,
        user_id=usuario_id,
        refresh_token_hash="hash",
        jti=uuid4(),
        issued_at=now,
        expires_at=now + timedelta(days=1),
        id=session_id,
    )
    session.add(s)
    await session.flush()

    return usuario_id, session_id
