from __future__ import annotations

import os
from uuid import UUID, uuid4

import pytest_asyncio
import sqlalchemy
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

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
    t = Tenant(codigo="TENANT-MSG", nombre="Mensajes Test Tenant", estado=TenantEstado.ACTIVO)
    session.add(t)
    await session.flush()
    return t


async def _create_usuario(session, tenant_id: UUID, **extra) -> Usuario:
    data = {
        "nombre": "Usuario",
        "apellidos": "Test",
        "email": f"user.{uuid4().hex[:8]}@test.com",
        "dni": "87654321",
        "cuil": "20-87654321-9",
        "cbu": "0000003100012345678902",
    }
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
