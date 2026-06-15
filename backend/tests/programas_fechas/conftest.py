"""Fixtures compartidos para tests de programas y fechas academicas (C-17 SS5)."""

from __future__ import annotations

import os

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/activia_trace_test"
)

from datetime import date, datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest_asyncio
import sqlalchemy
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.security.hashing import hash_email_for_search
from app.core.security.jwt import encode_access_token
from app.core.security.passwords import hash_password
from app.models.base import Base
from app.models.carrera import Carrera, CarreraEstado
from app.models.cohorte import Cohorte, CohorteEstado
from app.models.materia import Materia, MateriaEstado
from app.models.tenant import Tenant, TenantEstado


@pytest_asyncio.fixture
async def db_setup():
    from app.models import tenant  # noqa: F401
    from app.models import carrera, cohorte, materia  # noqa: F401
    from app.models import programa_materia, fecha_academica  # noqa: F401
    from app.rbac import models as _rbac_models  # noqa: F401
    from app.auth import models as _auth_models  # noqa: F401

    engine = create_async_engine(os.environ["DATABASE_URL"])
    async with engine.begin() as conn:
        # TODO: (HACK) SQL raw con CASCADE en lugar de Base.metadata.drop_all() — ver
        # backend/tests/calificaciones/conftest.py para explicación completa.
        await conn.execute(sqlalchemy.text("""
            DO $$ DECLARE r RECORD; BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename <> 'alembic_version') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """))
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    yield factory
    await engine.dispose()


async def _create_tenant(session) -> Tenant:
    t = Tenant(codigo="PF-TEST", nombre="Programas Fechas Test", estado=TenantEstado.ACTIVO)
    session.add(t)
    await session.flush()
    return t


async def _create_tenant_named(session, codigo: str, nombre: str) -> Tenant:
    t = Tenant(codigo=codigo, nombre=nombre, estado=TenantEstado.ACTIVO)
    session.add(t)
    await session.flush()
    return t


async def _create_carrera(session, tid: UUID) -> Carrera:
    c = Carrera(tenant_id=tid, codigo="ING-INF", nombre="Ingenieria en Informatica", estado=CarreraEstado.ACTIVA)
    session.add(c)
    await session.flush()
    return c


async def _create_cohorte(session, tid: UUID, carrera_id: UUID) -> Cohorte:
    c = Cohorte(
        tenant_id=tid,
        carrera_id=carrera_id,
        nombre="Cohorte 2025",
        anio=2025,
        vig_desde=date(2025, 3, 1),
        vig_hasta=date(2025, 12, 31),
        estado=CohorteEstado.ACTIVA,
    )
    session.add(c)
    await session.flush()
    return c


async def _create_materia(session, tid: UUID) -> Materia:
    m = Materia(tenant_id=tid, codigo="ALG-101", nombre="Algoritmos I", estado=MateriaEstado.ACTIVA)
    session.add(m)
    await session.flush()
    return m


async def _create_user_and_session(session, tenant_id: UUID) -> tuple[UUID, UUID, UUID]:
    from app.auth.models import AuthSession, AuthUser

    user_id = uuid4()
    u = AuthUser(
        id=user_id,
        tenant_id=tenant_id,
        email_enc="enc:test@test.com",
        email_hash=hash_email_for_search("test@test.com", tenant_id),
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
    return user_id, tenant_id, session_id


def _mint_jwt(user_id: UUID, tenant_id: UUID, session_id: UUID) -> str:
    return encode_access_token(
        user_id=user_id,
        tenant_id=tenant_id,
        session_id=session_id,
        jti=uuid4(),
    )
