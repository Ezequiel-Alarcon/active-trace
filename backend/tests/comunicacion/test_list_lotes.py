"""Strict TDD for listing communication batches grouped by lote."""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
import sqlalchemy
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.models import AuthSession, AuthUser
from app.core.security.hashing import hash_email_for_search
from app.core.security.jwt import encode_access_token
from app.main import app
from app.models.asignacion import Asignacion, ContextoTipo
from app.models.base import Base
from app.models.tenant import Tenant, TenantEstado
from app.modules.comunicacion.models.comunicacion import Comunicacion, ComunicacionEstado
from app.modules.comunicacion.repositories.comunicacion import ComunicacionRepository
from app.rbac.models import Permiso, Rol, RolPermiso

pytestmark = pytest.mark.no_db


@pytest_asyncio.fixture
async def db_setup(_reset_app_engine_async):  # noqa: F811
    """Bring up an isolated schema in the test database and yield a session factory."""
    from app.models import tenant  # noqa: F401
    from app.models import usuario, asignacion, carrera, cohorte, materia  # noqa: F401
    from app.rbac import models as _rbac_models  # noqa: F401
    from app.auth import models as _auth_models  # noqa: F401
    from app.audit import models as _audit_models  # noqa: F401
    from app.modules.comunicacion.models import comunicacion as _comunicacion_models  # noqa: F401

    engine = create_async_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.execute(sqlalchemy.text("""
            DO $$ DECLARE r RECORD; BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename <> 'alembic_version') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """))
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    try:
        yield factory
    finally:
        await engine.dispose()


async def _seed_tenant(session, codigo: str) -> Tenant:
    from app.rbac.constants import GLOBAL_TENANT_ID

    existing = await session.get(Tenant, GLOBAL_TENANT_ID)
    if existing is None:
        session.add(
            Tenant(
                id=GLOBAL_TENANT_ID,
                codigo="GLOBAL",
                nombre="Global System Tenant",
                estado=TenantEstado.ACTIVO,
            )
        )
        await session.flush()

    tenant = Tenant(codigo=codigo, nombre=f"Tenant {codigo}", estado=TenantEstado.ACTIVO)
    session.add(tenant)
    await session.flush()
    return tenant


async def _make_auth_user(session, tenant_id: UUID, email: str) -> AuthUser:
    user = AuthUser(
        tenant_id=tenant_id,
        email_enc=f"enc:{email}",
        email_hash=hash_email_for_search(email, tenant_id),
        password_hash="hash-placeholder",
    )
    session.add(user)
    await session.flush()
    return user


async def _make_session(session, user_id: UUID, tenant_id: UUID) -> AuthSession:
    now = datetime.now(timezone.utc)
    auth_session = AuthSession(
        tenant_id=tenant_id,
        user_id=user_id,
        refresh_token_hash="hash",
        jti=uuid4(),
        issued_at=now,
        expires_at=now + timedelta(days=1),
    )
    session.add(auth_session)
    await session.flush()
    return auth_session


async def _grant_permission(
    session, tenant_id: UUID, user_id: UUID, permission: str
) -> None:
    modulo, accion = permission.split(":", 1)
    role = Rol(tenant_id=tenant_id, nombre="COORDINADOR", descripcion="Coordinador")
    session.add(role)
    await session.flush()

    permiso = Permiso(tenant_id=tenant_id, modulo=modulo, accion=accion)
    session.add(permiso)
    await session.flush()

    session.add(RolPermiso(tenant_id=tenant_id, rol_id=role.id, permiso_id=permiso.id))
    session.add(
        Asignacion(
            tenant_id=tenant_id,
            usuario_id=user_id,
            rol_id=role.id,
            contexto_tipo=ContextoTipo.GLOBAL,
            contexto_id=None,
            desde=date(2024, 1, 1),
        )
    )
    await session.flush()


def _mint_jwt(user_id: UUID, tenant_id: UUID, session_id: UUID) -> str:
    return encode_access_token(
        user_id=user_id,
        tenant_id=tenant_id,
        session_id=session_id,
        jti=uuid4(),
    )


async def _make_comunicacion(
    session,
    *,
    tenant_id: UUID,
    lote_id: UUID | None,
    estado: ComunicacionEstado,
    asunto: str,
    cuerpo: str,
    destinatario: str,
    created_at: datetime | None = None,
) -> Comunicacion:
    comunicacion = Comunicacion(
        tenant_id=tenant_id,
        lote_id=lote_id,
        asunto=asunto,
        cuerpo=cuerpo,
        destinatario=f"placeholder-{uuid4()}@test.com",
        estado=estado,
        created_at=created_at,
    )
    comunicacion.set_destinatario(destinatario)
    session.add(comunicacion)
    await session.flush()
    return comunicacion


@pytest.mark.asyncio
async def test_list_lotes_grouped_returns_all_lotes_with_counts_and_first_message_metadata(
    db_setup,
) -> None:
    async with db_setup() as session:
        tenant = await _seed_tenant(session, "COM-ALL")
        lote_old = uuid4()
        lote_new = uuid4()
        base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)

        await _make_comunicacion(
            session,
            tenant_id=tenant.id,
            lote_id=lote_old,
            estado=ComunicacionEstado.PENDIENTE,
            asunto="Asunto inicial",
            cuerpo="Cuerpo inicial",
            destinatario="alpha@test.com",
            created_at=base_time,
        )
        await _make_comunicacion(
            session,
            tenant_id=tenant.id,
            lote_id=lote_old,
            estado=ComunicacionEstado.ENVIADO,
            asunto="Asunto posterior",
            cuerpo="Cuerpo posterior",
            destinatario="beta@test.com",
            created_at=base_time + timedelta(minutes=1),
        )
        await _make_comunicacion(
            session,
            tenant_id=tenant.id,
            lote_id=lote_old,
            estado=ComunicacionEstado.PENDIENTE,
            asunto="Asunto duplicado",
            cuerpo="Cuerpo duplicado",
            destinatario="alpha@test.com",
            created_at=base_time + timedelta(minutes=2),
        )
        await _make_comunicacion(
            session,
            tenant_id=tenant.id,
            lote_id=lote_new,
            estado=ComunicacionEstado.ERROR,
            asunto="Otro asunto",
            cuerpo="Otro cuerpo",
            destinatario="gamma@test.com",
            created_at=base_time + timedelta(minutes=3),
        )
        await _make_comunicacion(
            session,
            tenant_id=tenant.id,
            lote_id=None,
            estado=ComunicacionEstado.PENDIENTE,
            asunto="Sin lote",
            cuerpo="Sin lote",
            destinatario="ignore@test.com",
            created_at=base_time + timedelta(minutes=4),
        )
        await session.commit()

        repo = ComunicacionRepository(session, tenant.id)
        result = await repo.list_lotes_grouped(tenant.id)

    assert [row["lote_id"] for row in result] == [lote_new, lote_old]

    latest = result[0]
    assert latest["tenant_id"] == tenant.id
    assert latest["total"] == 1
    assert latest["pendientes"] == 0
    assert latest["enviando"] == 0
    assert latest["enviados"] == 0
    assert latest["errores"] == 1
    assert latest["cancelados"] == 0
    assert latest["asunto"] == "Otro asunto"
    assert latest["cuerpo"] == "Otro cuerpo"
    assert latest["destinatarios"] == ["gamma@test.com"]

    first = result[1]
    assert first["total"] == 3
    assert first["pendientes"] == 2
    assert first["enviando"] == 0
    assert first["enviados"] == 1
    assert first["errores"] == 0
    assert first["cancelados"] == 0
    assert first["asunto"] == "Asunto inicial"
    assert first["cuerpo"] == "Cuerpo inicial"
    assert first["destinatarios"] == ["alpha@test.com", "beta@test.com"]


@pytest.mark.asyncio
async def test_list_lotes_grouped_filters_by_estado_but_preserves_all_counts(db_setup) -> None:
    async with db_setup() as session:
        tenant = await _seed_tenant(session, "COM-FILTER")
        lote_pending = uuid4()
        lote_sent_only = uuid4()

        await _make_comunicacion(
            session,
            tenant_id=tenant.id,
            lote_id=lote_pending,
            estado=ComunicacionEstado.PENDIENTE,
            asunto="Pendiente",
            cuerpo="Pendiente",
            destinatario="pending@test.com",
        )
        await _make_comunicacion(
            session,
            tenant_id=tenant.id,
            lote_id=lote_pending,
            estado=ComunicacionEstado.ENVIADO,
            asunto="Pendiente enviado",
            cuerpo="Pendiente enviado",
            destinatario="mixed@test.com",
        )
        await _make_comunicacion(
            session,
            tenant_id=tenant.id,
            lote_id=lote_sent_only,
            estado=ComunicacionEstado.ENVIADO,
            asunto="Solo enviado",
            cuerpo="Solo enviado",
            destinatario="sent@test.com",
        )
        await session.commit()

        repo = ComunicacionRepository(session, tenant.id)
        result = await repo.list_lotes_grouped(tenant.id, ComunicacionEstado.PENDIENTE)

    assert len(result) == 1
    assert result[0]["lote_id"] == lote_pending
    assert result[0]["total"] == 2
    assert result[0]["pendientes"] == 1
    assert result[0]["enviados"] == 1


@pytest.mark.asyncio
async def test_list_lotes_grouped_returns_empty_when_no_matches(db_setup) -> None:
    async with db_setup() as session:
        tenant = await _seed_tenant(session, "COM-EMPTY")
        repo = ComunicacionRepository(session, tenant.id)

        result = await repo.list_lotes_grouped(tenant.id, ComunicacionEstado.PENDIENTE)

    assert result == []


@pytest.mark.asyncio
async def test_list_lotes_grouped_is_tenant_scoped(db_setup) -> None:
    async with db_setup() as session:
        tenant_a = await _seed_tenant(session, "COM-A")
        tenant_b = await _seed_tenant(session, "COM-B")
        lote_a = uuid4()

        await _make_comunicacion(
            session,
            tenant_id=tenant_a.id,
            lote_id=lote_a,
            estado=ComunicacionEstado.PENDIENTE,
            asunto="Tenant A",
            cuerpo="Tenant A",
            destinatario="a@test.com",
        )
        await _make_comunicacion(
            session,
            tenant_id=tenant_b.id,
            lote_id=uuid4(),
            estado=ComunicacionEstado.PENDIENTE,
            asunto="Tenant B",
            cuerpo="Tenant B",
            destinatario="b@test.com",
        )
        await session.commit()

        repo = ComunicacionRepository(session, tenant_a.id)
        result = await repo.list_lotes_grouped(tenant_a.id)

    assert len(result) == 1
    assert result[0]["lote_id"] == lote_a
    assert result[0]["tenant_id"] == tenant_a.id


@pytest.mark.asyncio
async def test_get_lotes_returns_pending_batches_for_current_tenant(db_setup) -> None:
    async with db_setup() as session:
        tenant = await _seed_tenant(session, "COM-API")
        lote_id = uuid4()
        other_lote_id = uuid4()
        base_time = datetime(2024, 2, 1, tzinfo=timezone.utc)

        user = await _make_auth_user(session, tenant.id, "coord@test.com")
        auth_session = await _make_session(session, user.id, tenant.id)
        await _grant_permission(session, tenant.id, user.id, "comunicacion:aprobar")

        await _make_comunicacion(
            session,
            tenant_id=tenant.id,
            lote_id=lote_id,
            estado=ComunicacionEstado.PENDIENTE,
            asunto="Asunto visible",
            cuerpo="Cuerpo visible",
            destinatario="uno@test.com",
            created_at=base_time,
        )
        await _make_comunicacion(
            session,
            tenant_id=tenant.id,
            lote_id=lote_id,
            estado=ComunicacionEstado.ENVIADO,
            asunto="Otro asunto",
            cuerpo="Otro cuerpo",
            destinatario="dos@test.com",
            created_at=base_time + timedelta(minutes=1),
        )
        await _make_comunicacion(
            session,
            tenant_id=tenant.id,
            lote_id=other_lote_id,
            estado=ComunicacionEstado.ENVIADO,
            asunto="No pending",
            cuerpo="No pending",
            destinatario="tres@test.com",
            created_at=base_time + timedelta(minutes=2),
        )
        await session.commit()

    token = _mint_jwt(user.id, tenant.id, auth_session.id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/comunicaciones/lotes?estado=Pendiente",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0] == {
        "lote_id": str(lote_id),
        "tenant_id": str(tenant.id),
        "total": 2,
        "pendientes": 1,
        "enviando": 0,
        "enviados": 1,
        "errores": 0,
        "cancelados": 0,
        "asunto": "Asunto visible",
        "cuerpo": "Cuerpo visible",
        "destinatarios": ["dos@test.com", "uno@test.com"],
    }


@pytest.mark.asyncio
async def test_get_lotes_returns_empty_array_when_no_batches_match(db_setup) -> None:
    async with db_setup() as session:
        tenant = await _seed_tenant(session, "COM-API-EMPTY")
        user = await _make_auth_user(session, tenant.id, "empty@test.com")
        auth_session = await _make_session(session, user.id, tenant.id)
        await _grant_permission(session, tenant.id, user.id, "comunicacion:aprobar")
        await session.commit()

    token = _mint_jwt(user.id, tenant.id, auth_session.id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/comunicaciones/lotes?estado=Pendiente",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_lotes_returns_403_without_permission(db_setup) -> None:
    async with db_setup() as session:
        tenant = await _seed_tenant(session, "COM-API-403")
        user = await _make_auth_user(session, tenant.id, "noperm@test.com")
        auth_session = await _make_session(session, user.id, tenant.id)
        await session.commit()

    token = _mint_jwt(user.id, tenant.id, auth_session.id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/comunicaciones/lotes",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 403
