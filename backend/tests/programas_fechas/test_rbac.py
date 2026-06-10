"""Strict TDD for RBAC on programas_fechas endpoints (C-17 SS5.5).

Tests verify that endpoints return 403 without estructura:gestionar and 2xx with it.
Uses HTTP-level testing via httpx.AsyncClient with FastAPI dependency overrides.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from app.auth.models import AuthSession, AuthUser
from app.core.dependencies import get_db
from app.core.security.hashing import hash_email_for_search
from app.core.security.jwt import encode_access_token
from app.core.security.passwords import hash_password
from app.core.tenancy import TenantContext, set_tenant_context, reset_tenant_context
from app.models.tenant import Tenant, TenantEstado
from app.rbac.models import Permiso, Rol, RolPermiso
from app.routers.programas_fechas import router as programas_fechas_router
from tests.programas_fechas.conftest import db_setup

pytestmark = [pytest.mark.asyncio, pytest.mark.no_db]


async def _create_tenant(session) -> Tenant:
    t = Tenant(codigo="RBAC-TEST", nombre="RBAC Test Tenant", estado=TenantEstado.ACTIVO)
    session.add(t)
    await session.flush()
    return t


async def _create_auth_user(session, tenant_id, email="rbac@test.com"):
    u = AuthUser(
        tenant_id=tenant_id,
        email_enc=f"enc:{email}",
        email_hash=hash_email_for_search(email, tenant_id),
        password_hash=hash_password("Pa55word!"),
    )
    session.add(u)
    await session.flush()
    return u


async def _create_auth_session(session, tenant_id, user_id):
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    s = AuthSession(
        tenant_id=tenant_id,
        user_id=user_id,
        refresh_token_hash="hash",
        jti=uuid4(),
        issued_at=now,
        expires_at=now + timedelta(days=1),
    )
    session.add(s)
    await session.flush()
    return s


def _mint_jwt(user_id, tenant_id, session_id):
    return encode_access_token(
        user_id=user_id,
        tenant_id=tenant_id,
        session_id=session_id,
        jti=uuid4(),
    )


@pytest_asyncio.fixture
async def app_client(db_setup):
    app = FastAPI()
    app.include_router(programas_fechas_router)

    async def override_get_db():
        async with db_setup() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()


async def test_list_programas_without_perm_returns_403(app_client, db_setup) -> None:
    async with db_setup() as session:
        tenant = await _create_tenant(session)
        user = await _create_auth_user(session, tenant.id)
        sess = await _create_auth_session(session, tenant.id, user.id)
        await session.commit()
        token = _mint_jwt(user.id, tenant.id, sess.id)

    resp = await app_client.get(
        "/api/programas",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


async def test_create_programa_without_perm_returns_403(app_client, db_setup) -> None:
    async with db_setup() as session:
        tenant = await _create_tenant(session)
        user = await _create_auth_user(session, tenant.id)
        sess = await _create_auth_session(session, tenant.id, user.id)
        await session.commit()
        token = _mint_jwt(user.id, tenant.id, sess.id)

    resp = await app_client.post(
        "/api/programas",
        json={
            "materia_id": str(uuid4()),
            "carrera_id": str(uuid4()),
            "cohorte_id": str(uuid4()),
            "titulo": "Test",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


async def test_get_programa_without_perm_returns_403(app_client, db_setup) -> None:
    async with db_setup() as session:
        tenant = await _create_tenant(session)
        user = await _create_auth_user(session, tenant.id)
        sess = await _create_auth_session(session, tenant.id, user.id)
        await session.commit()
        token = _mint_jwt(user.id, tenant.id, sess.id)

    resp = await app_client.get(
        f"/api/programas/{uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


async def test_patch_programa_without_perm_returns_403(app_client, db_setup) -> None:
    async with db_setup() as session:
        tenant = await _create_tenant(session)
        user = await _create_auth_user(session, tenant.id)
        sess = await _create_auth_session(session, tenant.id, user.id)
        await session.commit()
        token = _mint_jwt(user.id, tenant.id, sess.id)

    resp = await app_client.patch(
        f"/api/programas/{uuid4()}",
        json={"titulo": "New"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


async def test_delete_programa_without_perm_returns_403(app_client, db_setup) -> None:
    async with db_setup() as session:
        tenant = await _create_tenant(session)
        user = await _create_auth_user(session, tenant.id)
        sess = await _create_auth_session(session, tenant.id, user.id)
        await session.commit()
        token = _mint_jwt(user.id, tenant.id, sess.id)

    resp = await app_client.delete(
        f"/api/programas/{uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


async def test_list_fechas_without_perm_returns_403(app_client, db_setup) -> None:
    async with db_setup() as session:
        tenant = await _create_tenant(session)
        user = await _create_auth_user(session, tenant.id)
        sess = await _create_auth_session(session, tenant.id, user.id)
        await session.commit()
        token = _mint_jwt(user.id, tenant.id, sess.id)

    resp = await app_client.get(
        "/api/fechas-academicas",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


async def test_create_fecha_without_perm_returns_403(app_client, db_setup) -> None:
    async with db_setup() as session:
        tenant = await _create_tenant(session)
        user = await _create_auth_user(session, tenant.id)
        sess = await _create_auth_session(session, tenant.id, user.id)
        await session.commit()
        token = _mint_jwt(user.id, tenant.id, sess.id)

    resp = await app_client.post(
        "/api/fechas-academicas",
        json={
            "materia_id": str(uuid4()),
            "cohorte_id": str(uuid4()),
            "tipo": "Parcial",
            "numero_instancia": 1,
            "fecha": "2025-06-15",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


async def test_fragmento_lms_without_perm_returns_403(app_client, db_setup) -> None:
    async with db_setup() as session:
        tenant = await _create_tenant(session)
        user = await _create_auth_user(session, tenant.id)
        sess = await _create_auth_session(session, tenant.id, user.id)
        await session.commit()
        token = _mint_jwt(user.id, tenant.id, sess.id)

    resp = await app_client.get(
        "/api/fechas-academicas/fragmento-lms",
        params={"materia_id": str(uuid4()), "cohorte_id": str(uuid4())},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


async def test_list_programas_with_perm_returns_200(app_client, db_setup) -> None:
    async with db_setup() as session:
        tenant = await _create_tenant(session)
        tid = tenant.id
        rol = Rol(tenant_id=tid, nombre="ADMIN", descripcion="Admin")
        session.add(rol)
        await session.flush()
        perm = Permiso(tenant_id=tid, modulo="estructura", accion="gestionar")
        session.add(perm)
        await session.flush()
        session.add(RolPermiso(tenant_id=tid, rol_id=rol.id, permiso_id=perm.id))
        user = await _create_auth_user(session, tid)
        sess = await _create_auth_session(session, tid, user.id)
        await session.commit()
        token = _mint_jwt(user.id, tid, sess.id)

    resp = await app_client.get(
        "/api/programas",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert data == []


async def test_create_programa_with_perm_returns_201(app_client, db_setup) -> None:
    from app.models.carrera import Carrera, CarreraEstado
    from app.models.cohorte import Cohorte, CohorteEstado
    from app.models.materia import Materia, MateriaEstado
    from datetime import date

    async with db_setup() as session:
        tenant = await _create_tenant(session)
        tid = tenant.id
        rol = Rol(tenant_id=tid, nombre="ADMIN", descripcion="Admin")
        session.add(rol)
        await session.flush()
        perm = Permiso(tenant_id=tid, modulo="estructura", accion="gestionar")
        session.add(perm)
        await session.flush()
        session.add(RolPermiso(tenant_id=tid, rol_id=rol.id, permiso_id=perm.id))
        user = await _create_auth_user(session, tid)
        sess = await _create_auth_session(session, tid, user.id)

        carrera = Carrera(tenant_id=tid, codigo="ING-INF", nombre="Ingenieria", estado=CarreraEstado.ACTIVA)
        session.add(carrera)
        await session.flush()
        cohorte = Cohorte(
            tenant_id=tid, carrera_id=carrera.id, nombre="Cohorte 2025",
            anio=2025, vig_desde=date(2025, 3, 1), vig_hasta=date(2025, 12, 31),
            estado=CohorteEstado.ACTIVA,
        )
        session.add(cohorte)
        await session.flush()
        materia = Materia(tenant_id=tid, codigo="ALG-101", nombre="Algoritmos I", estado=MateriaEstado.ACTIVA)
        session.add(materia)
        await session.flush()
        await session.commit()
        token = _mint_jwt(user.id, tid, sess.id)

    resp = await app_client.post(
        "/api/programas",
        json={
            "materia_id": str(materia.id),
            "carrera_id": str(carrera.id),
            "cohorte_id": str(cohorte.id),
            "titulo": "Programa RBAC Test",
            "referencia_archivo": "/files/test.pdf",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["titulo"] == "Programa RBAC Test"
    assert data["tenant_id"] == str(tid)
