"""Padron integration tests (T-7.1 to T-7.8).

Tests versionado, import, isolation, and vaciar_datos.
Uses a real test database via the _apply_schema_once fixture.
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.usuario import Usuario
from app.repositories.padron import PadronRepository
from app.schemas.padron import EntradaPadronCreate, VersionPadronCreate
from app.services.padron import PadronService


@pytest.mark.usefixtures("_apply_schema_once")
class TestVersionado:
    async def test_activar_version_desactiva_anterior(
        self, db_session, tenant_a, user_admin_a
    ):
        """T-7.1: Activating V2 deactivates V1 for same materia-cohorte."""
        materia_id = (await _create_materia(db_session, tenant_a)).id
        cohorte_id = (await _create_cohorte(db_session, tenant_a)).id

        repo = PadronRepository(db_session, tenant_a)

        v1 = await repo.create_version_and_entries(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            cargado_por=user_admin_a,
            entradas_data=[
                {"nombre": "Alumno", "apellidos": "Uno", "email": "a1@test.com"}
            ],
        )

        v2 = await repo.create_version_and_entries(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            cargado_por=user_admin_a,
            entradas_data=[
                {"nombre": "Alumno", "apellidos": "Dos", "email": "a2@test.com"}
            ],
        )

        # Deactivate V1, activate V2
        await repo.deactivate_all(materia_id, cohorte_id, version_id_except=v2.id)

        # Reload v1 from DB
        await db_session.refresh(v1)
        await db_session.refresh(v2)

        assert v1.activa is False
        assert v2.activa is True

    async def test_primer_version_se_activa_ok(self, db_session, tenant_a, user_admin_a):
        """Only version activates without error."""
        materia_id = (await _create_materia(db_session, tenant_a)).id
        cohorte_id = (await _create_cohorte(db_session, tenant_a)).id

        repo = PadronRepository(db_session, tenant_a)
        v1 = await repo.create_version_and_entries(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            cargado_por=user_admin_a,
            entradas_data=[
                {"nombre": "Alumno", "apellidos": "Test", "email": "test@test.com"}
            ],
        )
        await repo.deactivate_all(materia_id, cohorte_id, version_id_except=v1.id)
        await db_session.refresh(v1)
        assert v1.activa is True


@pytest.mark.usefixtures("_apply_schema_once")
class TestEntradaSinUsuario:
    async def test_entrada_sin_usuario_id_se_persiste_como_null(
        self, db_session, tenant_a, user_admin_a
    ):
        """T-7.3: EntradaPadron with no matching usuario persists usuario_id=None."""
        materia_id = (await _create_materia(db_session, tenant_a)).id
        cohorte_id = (await _create_cohorte(db_session, tenant_a)).id

        repo = PadronRepository(db_session, tenant_a)
        version = await repo.create_version_and_entries(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            cargado_por=user_admin_a,
            entradas_data=[
                {
                    "nombre": "Sin Cuenta",
                    "apellidos": "Alumno",
                    "email": "sin-cuenta@test.com",
                    "usuario_id": None,
                }
            ],
        )

        entradas = await repo.get_entries_by_version(version.id)
        assert len(entradas) == 1
        from app.repositories.padron import decrypt_entrada_email
        assert entradas[0].usuario_id is None
        assert decrypt_entrada_email(entradas[0]) == "sin-cuenta@test.com"


@pytest.mark.usefixtures("_apply_schema_once")
class TestImportPadron:
    async def test_import_padron_crea_version_y_entradas(
        self, db_session, tenant_a, user_admin_a
    ):
        """T-7.2: Import creates version + entries atomically."""
        materia_id = (await _create_materia(db_session, tenant_a)).id
        cohorte_id = (await _create_cohorte(db_session, tenant_a)).id

        svc = PadronService(db_session, tenant_a)
        data = VersionPadronCreate(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            entradas=[
                EntradaPadronCreate(nombre="Juan", apellidos="Pérez", email="juan@test.com"),
                EntradaPadronCreate(nombre="María", apellidos="García", email="maria@test.com"),
            ],
        )

        version = await svc.import_padron(data, user_admin_a)

        assert version.tenant_id == tenant_a
        assert version.materia_id == materia_id
        assert version.cohorte_id == cohorte_id
        assert version.cargado_por == user_admin_a
        assert version.activa is True

        repo = PadronRepository(db_session, tenant_a)
        entradas = await repo.get_entries_by_version(version.id)
        assert len(entradas) == 2


@pytest.mark.usefixtures("_apply_schema_once")
class TestAislamientoTenant:
    async def test_tenant_a_no_ve_padron_de_tenant_b(
        self, db_session, tenant_a, tenant_b, user_admin_a, user_admin_b
    ):
        """T-7.4: Tenant isolation on padron data."""
        # Create materia in both tenants
        mat_a = await _create_materia(db_session, tenant_a)
        mat_b = await _create_materia(db_session, tenant_b)
        coh_a = await _create_cohorte(db_session, tenant_a)
        coh_b = await _create_cohorte(db_session, tenant_b)

        # Import padron for tenant A
        repo_a = PadronRepository(db_session, tenant_a)
        v_a = await repo_a.create_version_and_entries(
            materia_id=mat_a.id,
            cohorte_id=coh_a.id,
            cargado_por=user_admin_a,
            entradas_data=[{"nombre": "A", "apellidos": "Test", "email": "a@test.com"}],
        )

        # Import padron for tenant B
        repo_b = PadronRepository(db_session, tenant_b)
        await repo_b.create_version_and_entries(
            materia_id=mat_b.id,
            cohorte_id=coh_b.id,
            cargado_por=user_admin_b,
            entradas_data=[{"nombre": "B", "apellidos": "Test", "email": "b@test.com"}],
        )

        # Tenant A queries
        versions_a = await repo_a.list_by_materia_cohorte(mat_a.id, coh_a.id)
        assert len(versions_a) == 1
        assert versions_a[0].id == v_a.id

        # Tenant A should NOT see tenant B's data
        versions_b_from_a = await repo_a.list_by_materia_cohorte(mat_b.id, coh_b.id)
        assert len(versions_b_from_a) == 0


@pytest.mark.usefixtures("_apply_schema_once")
class TestVaciarDatos:
    async def test_vaciar_datos_soft_deleta_todo(
        self, db_session, tenant_a, user_admin_a
    ):
        """T-7.7: Vaciar datos soft-deletes all versions and entries."""
        materia_id = (await _create_materia(db_session, tenant_a)).id
        cohorte_id = (await _create_cohorte(db_session, tenant_a)).id

        repo = PadronRepository(db_session, tenant_a)
        await repo.create_version_and_entries(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            cargado_por=user_admin_a,
            entradas_data=[
                {"nombre": "Alumno", "apellidos": "Test", "email": "test@test.com"}
            ],
        )

        count = await repo.vaciar_datos(materia_id, cohorte_id)

        assert count >= 1
        versions = await repo.list_by_materia_cohorte(materia_id, cohorte_id)
        assert len(versions) == 0  # soft deleted


@pytest.mark.usefixtures("_apply_schema_once")
class TestPadronServicePreview:
    async def test_preview_sin_matching_usuario(
        self, db_session, tenant_a, user_admin_a
    ):
        """Preview returns matched_usuario_id=None when no user matches."""
        svc = PadronService(db_session, tenant_a)
        content = b"Nombre,Apellidos,Email\nJuan,Perez,juan@unknown.com"
        usuario_ids_by_email = {}  # no matching users

        result = await svc.preview(content, "test.csv", usuario_ids_by_email)

        assert result.total == 1
        assert result.rows[0].matched_usuario_id is None
        assert result.rows[0].nombre == "Juan"

    async def test_preview_con_matching_usuario(
        self, db_session, tenant_a, user_admin_a
    ):
        """Preview returns matched_usuario_id when user exists."""
        # Create a usuario first
        user = await _create_usuario(db_session, tenant_a, email="juan@matching.com")

        from app.core.security.hashing import hash_email_for_search
        svc = PadronService(db_session, tenant_a)
        content = b"Nombre,Apellidos,Email\nJuan,Perez,juan@matching.com"
        # TODO: (FIX) El lookup de usuario por email usa email_hash (HMAC del email
        # cifrado, con scope de tenant) y NO el email en texto plano. La DB solo
        # almacena el hash — nunca el email legible — por diseño PII. El dict
        # usuario_ids_by_email debe ser {email_hash: user_id}, no {email: user_id}.
        email_hash = hash_email_for_search("juan@matching.com", tenant_a)
        usuario_ids_by_email = {email_hash: user.id}

        result = await svc.preview(content, "test.csv", usuario_ids_by_email)

        assert result.total == 1
        assert result.rows[0].matched_usuario_id == user.id


# ─── Helpers ────────────────────────────────────────────────────────────────


async def _create_materia(session, tenant_id) -> Materia:
    materia = Materia(
        tenant_id=tenant_id,
        codigo=f"M-{uuid4().hex[:6]}",
        nombre="Materia Test",
        estado="Activa",
    )
    session.add(materia)
    await session.flush()
    return materia


async def _create_cohorte(session, tenant_id) -> Cohorte:
    carrera = Carrera(
        tenant_id=tenant_id,
        codigo=f"C-{uuid4().hex[:6]}",
        nombre="Carrera Test",
        estado="Activa",
    )
    session.add(carrera)
    await session.flush()

    cohorte = Cohorte(
        tenant_id=tenant_id,
        carrera_id=carrera.id,
        nombre="TEST-2026",
        anio=2026,
        vig_desde=date.today(),
        vig_hasta=date.today() + timedelta(days=180),
        estado="Activa",
    )
    session.add(cohorte)
    await session.flush()
    return cohorte


async def _create_usuario(session, tenant_id, email) -> Usuario:
    from app.repositories.usuarios import encrypt_usuario_fields

    uid = uuid4()
    enc = encrypt_usuario_fields(
        {"email": email, "dni": "11111111", "cuil": "20-11111111-9", "cbu": "1111111111111111111111"},
        tenant_id=tenant_id,
    )
    usuario = Usuario(id=uid, tenant_id=tenant_id, nombre="Test", apellidos="User", **enc)
    session.add(usuario)
    await session.flush()
    return usuario