"""API regression tests for C-26 comisiones/import/analisis wiring."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
import sqlalchemy
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.v1.main_router import main_router
from app.auth.models import AuthSession, AuthUser
from app.core.dependencies import get_db
from app.core.security.hashing import hash_email_for_search
from app.core.security.jwt import encode_access_token
from app.core.security.passwords import hash_password
from app.models.base import Base
from app.models.carrera import Carrera, CarreraEstado
from app.models.cohorte import Cohorte, CohorteEstado
from app.models.materia import Materia, MateriaEstado
from app.models.padron import VersionPadron
from app.models.tenant import Tenant, TenantEstado
from app.models.usuario import Usuario
from app.rbac.models import Permiso, Rol, RolPermiso
from app.repositories.padron import PadronRepository
from app.repositories.usuarios import encrypt_usuario_fields


pytestmark = pytest.mark.usefixtures("_reset_app_engine_async")


@pytest_asyncio.fixture
async def db_setup():
    import os

    import app.models.asignacion  # noqa: F401
    import app.models.carrera  # noqa: F401
    import app.models.cohorte  # noqa: F401
    import app.models.materia  # noqa: F401
    import app.models.padron  # noqa: F401
    import app.models.tenant  # noqa: F401
    import app.models.usuario  # noqa: F401
    from app.auth import models as _auth_models  # noqa: F401
    from app.domain.calificaciones.models.calificacion import Calificacion  # noqa: F401
    from app.domain.calificaciones.models.umbral_materia import UmbralMateria  # noqa: F401
    from app.rbac import models as _rbac_models  # noqa: F401

    engine = create_async_engine(os.environ["DATABASE_URL"])
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


@pytest_asyncio.fixture
async def app_client(db_setup):
    app = FastAPI()
    app.include_router(main_router)

    async def override_get_db():
        async with db_setup() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


async def _tenant(session, codigo: str) -> Tenant:
    tenant = Tenant(codigo=codigo, nombre=codigo, estado=TenantEstado.ACTIVO)
    session.add(tenant)
    await session.flush()
    return tenant


async def _auth_user(session, tenant_id: UUID, email: str) -> AuthUser:
    user = AuthUser(
        tenant_id=tenant_id,
        email_enc=email,
        email_hash=hash_email_for_search(email, tenant_id),
        password_hash=hash_password("Pa55word!"),
    )
    session.add(user)
    await session.flush()
    return user


async def _profile_user(session, tenant_id: UUID, email: str, user_id: UUID | None = None) -> Usuario:
    encrypted = encrypt_usuario_fields(
        {"email": email, "dni": "11111111", "cuil": "20-11111111-9", "cbu": "1111111111111111111111"},
        tenant_id,
    )
    user = Usuario(
        id=user_id or uuid4(),
        tenant_id=tenant_id,
        nombre="Ada",
        apellidos="Lovelace",
        **encrypted,
    )
    session.add(user)
    await session.flush()
    return user


async def _auth_session(session, tenant_id: UUID, user_id: UUID) -> AuthSession:
    now = datetime.now(timezone.utc)
    auth_session = AuthSession(
        tenant_id=tenant_id,
        user_id=user_id,
        refresh_token_hash="test-refresh-hash",
        jti=uuid4(),
        issued_at=now,
        expires_at=now + timedelta(days=1),
    )
    session.add(auth_session)
    await session.flush()
    return auth_session


def _token(user_id: UUID, tenant_id: UUID, session_id: UUID) -> str:
    return encode_access_token(user_id=user_id, tenant_id=tenant_id, session_id=session_id, jti=uuid4())


async def _permission(session, tenant_id: UUID, permission: str) -> None:
    modulo, accion = permission.split(":", 1)
    rol = Rol(tenant_id=tenant_id, nombre=f"ROLE-{permission}")
    permiso = Permiso(tenant_id=tenant_id, modulo=modulo, accion=accion)
    session.add_all([rol, permiso])
    await session.flush()
    session.add(RolPermiso(tenant_id=tenant_id, rol_id=rol.id, permiso_id=permiso.id))
    await session.flush()


async def _academic_context(session, tenant_id: UUID, suffix: str) -> tuple[Materia, Cohorte]:
    carrera = Carrera(
        tenant_id=tenant_id,
        codigo=f"CAR-{suffix}",
        nombre=f"Carrera {suffix}",
        estado=CarreraEstado.ACTIVA,
    )
    materia = Materia(
        tenant_id=tenant_id,
        codigo=f"MAT-{suffix}",
        nombre=f"Materia {suffix}",
        estado=MateriaEstado.ACTIVA,
    )
    session.add_all([carrera, materia])
    await session.flush()
    cohorte = Cohorte(
        tenant_id=tenant_id,
        carrera_id=carrera.id,
        nombre=f"Cohorte {suffix}",
        anio=2026,
        vig_desde=date(2026, 1, 1),
        estado=CohorteEstado.ACTIVA,
    )
    session.add(cohorte)
    await session.flush()
    return materia, cohorte


async def _active_padron(
    session,
    tenant_id: UUID,
    materia: Materia,
    cohorte: Cohorte,
    cargado_por: UUID,
    alumno: Usuario,
    actividades: list[str] | None = None,
) -> VersionPadron:
    repo = PadronRepository(session, tenant_id)
    version = await repo.create_version_and_entries(
        materia.id,
        cohorte.id,
        cargado_por,
        [
            {
                "usuario_id": alumno.id,
                "nombre": alumno.nombre,
                "apellidos": alumno.apellidos,
                "email": "alumno@test.com",
            }
        ],
    )
    version.actividades = actividades or ["TP1", "TP2"]
    await session.flush()
    return version


async def _authorized_seed(session, permission: str = "analisis:ver") -> tuple[UUID, AuthUser, str]:
    tenant = await _tenant(session, f"T-{uuid4().hex[:8]}")
    auth = await _auth_user(session, tenant.id, "profesor@test.com")
    await _profile_user(session, tenant.id, "profesor@test.com", auth.id)
    await _permission(session, tenant.id, permission)
    sess = await _auth_session(session, tenant.id, auth.id)
    await session.commit()
    return tenant.id, auth, _token(auth.id, tenant.id, sess.id)


async def test_get_comisiones_returns_only_authenticated_tenant(app_client, db_setup):
    async with db_setup() as session:
        tenant_id, auth, token = await _authorized_seed(session, "analisis:ver")
        other = await _tenant(session, "OTHER-TENANT")
        alumno = await _profile_user(session, tenant_id, "alumno@test.com")
        materia, cohorte = await _academic_context(session, tenant_id, "A")
        await _active_padron(session, tenant_id, materia, cohorte, auth.id, alumno)
        other_user = await _profile_user(session, other.id, "other@test.com")
        other_materia, other_cohorte = await _academic_context(session, other.id, "B")
        await _active_padron(session, other.id, other_materia, other_cohorte, other_user.id, other_user)
        await session.commit()

    response = await app_client.get("/api/comisiones", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data == [
        {
            "id": f"{materia.id}:{cohorte.id}",
            "materia_id": str(materia.id),
            "materia_nombre": "Materia A",
            "cohorte_id": str(cohorte.id),
            "cohorte_nombre": "Cohorte A",
        }
    ]


async def test_get_comisiones_returns_empty_list(app_client, db_setup):
    async with db_setup() as session:
        _, _, token = await _authorized_seed(session, "analisis:ver")

    response = await app_client.get("/api/comisiones", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == []


async def test_get_comisiones_requires_authentication_and_permission(app_client, db_setup):
    assert (await app_client.get("/api/comisiones")).status_code == 401
    async with db_setup() as session:
        tenant = await _tenant(session, "NO-PERM")
        auth = await _auth_user(session, tenant.id, "noperm@test.com")
        sess = await _auth_session(session, tenant.id, auth.id)
        await session.commit()
        token = _token(auth.id, tenant.id, sess.id)

    response = await app_client.get("/api/comisiones", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403


async def test_analisis_endpoint_requires_permission(app_client, db_setup):
    async with db_setup() as session:
        tenant = await _tenant(session, "ANALISIS-NO-PERM")
        auth = await _auth_user(session, tenant.id, "noperm-analisis@test.com")
        sess = await _auth_session(session, tenant.id, auth.id)
        await session.commit()
        token = _token(auth.id, tenant.id, sess.id)

    response = await app_client.get(
        "/api/analisis/atrasados",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


async def test_import_confirm_persists_preview_rows_through_dependency_injection(app_client, db_setup):
    async with db_setup() as session:
        tenant_id, auth, token = await _authorized_seed(session, "calificaciones:importar")
        await _profile_user(session, tenant_id, "alumno@test.com")
        materia, _ = await _academic_context(session, tenant_id, "IMPORT")
        await session.commit()

    csv = f"usuario_email,materia_id,nota\nalumno@test.com,{materia.id},8\nmissing@test.com,{materia.id},4\n".encode()
    preview = await app_client.post(
        "/api/calificaciones/import/preview",
        params={"type": "grades"},
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("notas.csv", csv, "text/csv")},
    )
    assert preview.status_code == 200

    response = await app_client.post(
        "/api/calificaciones/import/confirm",
        headers={"Authorization": f"Bearer {token}"},
        json={"preview_token": preview.json()["preview_token"]},
    )

    assert response.status_code == 200
    assert response.json() == {"persisted": 1, "skipped": 0, "failed": 0}


async def test_analisis_atrasados_returns_seeded_delayed_students(app_client, db_setup):
    from app.domain.calificaciones.models.calificacion import Calificacion
    from app.domain.calificaciones.models.umbral_materia import UmbralMateria

    async with db_setup() as session:
        tenant_id, auth, token = await _authorized_seed(session, "analisis:ver")
        alumno = await _profile_user(session, tenant_id, "alumno@test.com")
        materia, cohorte = await _academic_context(session, tenant_id, "ATR")
        version = await _active_padron(session, tenant_id, materia, cohorte, auth.id, alumno)
        session.add(UmbralMateria(tenant_id=tenant_id, materia_id=materia.id, asignacion_id=None, umbral_pct=60, conjunto_aprobado=["A"]))
        session.add(Calificacion(tenant_id=tenant_id, materia_id=materia.id, usuario_id=alumno.id, version_padron_id=version.id, nota=4, origen="Importado"))
        await session.commit()

    response = await app_client.get(
        "/api/analisis/atrasados",
        params={"materia_id": str(materia.id)},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["alumnos"][0]["usuario_id"] == str(alumno.id)
    assert data["alumnos"][0]["email"] == "alumno@test.com"
    assert data["alumnos"][0]["estado"] == "atrasado"


async def test_ranking_counts_only_approved_by_threshold_and_orders_desc(app_client, db_setup):
    from app.domain.calificaciones.models.calificacion import Calificacion
    from app.domain.calificaciones.models.umbral_materia import UmbralMateria

    async with db_setup() as session:
        tenant_id, auth, token = await _authorized_seed(session, "analisis:ver")
        alumno_a = await _profile_user(session, tenant_id, "a@test.com")
        alumno_b = await _profile_user(session, tenant_id, "b@test.com")
        materia, _ = await _academic_context(session, tenant_id, "RANK")
        session.add(UmbralMateria(tenant_id=tenant_id, materia_id=materia.id, asignacion_id=None, umbral_pct=60, conjunto_aprobado=["A"]))
        session.add_all([
            Calificacion(tenant_id=tenant_id, materia_id=materia.id, usuario_id=alumno_a.id, asignacion_id=uuid4(), nota=9, origen="Importado"),
            Calificacion(tenant_id=tenant_id, materia_id=materia.id, usuario_id=alumno_a.id, asignacion_id=uuid4(), nota=3, origen="Importado"),
            Calificacion(tenant_id=tenant_id, materia_id=materia.id, usuario_id=alumno_b.id, asignacion_id=uuid4(), nota=7, origen="Importado"),
            Calificacion(tenant_id=tenant_id, materia_id=materia.id, usuario_id=alumno_b.id, asignacion_id=uuid4(), nota="A", origen="Importado"),
        ])
        await session.commit()

    response = await app_client.get(
        "/api/analisis/ranking",
        params={"materia_id": str(materia.id)},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    rankings = response.json()["rankings"]
    assert [row["usuario_id"] for row in rankings] == [str(alumno_b.id), str(alumno_a.id)]
    assert [row["cantidad_aprobadas"] for row in rankings] == [2, 1]


async def test_reportes_return_service_rows_instead_of_empty_stubs(app_client, db_setup):
    from app.domain.calificaciones.models.calificacion import Calificacion
    from app.domain.calificaciones.models.umbral_materia import UmbralMateria

    async with db_setup() as session:
        tenant_id, auth, token = await _authorized_seed(session, "reportes:ver")
        alumno = await _profile_user(session, tenant_id, "alumno@test.com")
        materia, cohorte = await _academic_context(session, tenant_id, "REP")
        version = await _active_padron(session, tenant_id, materia, cohorte, auth.id, alumno)
        session.add(UmbralMateria(tenant_id=tenant_id, materia_id=materia.id, asignacion_id=None, umbral_pct=60, conjunto_aprobado=["A"]))
        session.add(Calificacion(tenant_id=tenant_id, materia_id=materia.id, usuario_id=alumno.id, version_padron_id=version.id, nota=8, origen="Importado"))
        await session.commit()

    materia_response = await app_client.get(
        f"/api/reportes/materia/{materia.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    notas_response = await app_client.get(
        "/api/reportes/notas-finales",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert materia_response.status_code == 200
    assert materia_response.json()["materia_nombre"] == "Materia REP"
    assert len(materia_response.json()["alumnos"]) == 1
    assert notas_response.status_code == 200
    assert notas_response.json()["notas"][0]["materia_nombre"] == "Materia REP"
    assert notas_response.json()["notas"][0]["aprobados"] == 1
