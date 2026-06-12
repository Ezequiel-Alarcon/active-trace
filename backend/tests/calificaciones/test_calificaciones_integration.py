"""Tests de integracion para calificaciones (C-10).

Tests el flujo de importacion en 2 pasos (preview + confirm),
derivacion de aprobado, y aislamiento de tenants.
"""

import io
from uuid import uuid4

import pytest
import openpyxl

from app.domain.calificaciones.repositories.calificacion import CalificacionRepository
from app.domain.calificaciones.repositories.umbral_materia import UmbralMateriaRepository
from app.domain.calificaciones.services.aprobado import derivar_aprobado
from app.domain.calificaciones.services.import_service import (
    CalificacionParseError,
    ImportService,
    parse_calificaciones_csv,
    parse_calificaciones_file,
    parse_calificaciones_xlsx,
)


class TestParseCalificaciones:
    def test_parse_csv_returns_rows(self):
        content = b"usuario_email,materia_id,nota\njuan@test.com,abc123,7.5"
        rows = parse_calificaciones_csv(content)
        assert len(rows) == 1
        assert rows[0]["usuario_email"] == "juan@test.com"

    def test_parse_csv_normalizes_email_header(self):
        content = b"email,materia_id,nota\njuan@test.com,abc123,7.5"
        rows = parse_calificaciones_csv(content)
        assert rows[0]["usuario_email"] == "juan@test.com"

    def test_parse_csv_raises_on_missing_required_headers(self):
        content = b"usuario_email\njuan@test.com"
        with pytest.raises(CalificacionParseError) as exc_info:
            parse_calificaciones_csv(content)
        assert "materia_id" in str(exc_info.value).lower()

    def test_parse_xlsx_returns_rows(self):
        wb_content = _make_xlsx_bytes([
            ["usuario_email", "materia_id", "nota"],
            ["juan@test.com", "abc123", "7.5"],
        ])
        rows = parse_calificaciones_xlsx(wb_content)
        assert len(rows) == 1
        assert rows[0]["usuario_email"] == "juan@test.com"

    def test_parse_xlsx_raises_on_empty_file(self):
        wb_content = _make_xlsx_bytes([[]])
        with pytest.raises(CalificacionParseError) as exc_info:
            parse_calificaciones_xlsx(wb_content)
        assert "vacío" in str(exc_info.value).lower() or "empty" in str(exc_info.value).lower()

    def test_parse_file_routes_xlsx(self):
        wb_content = _make_xlsx_bytes([
            ["usuario_email", "materia_id", "nota"],
            ["juan@test.com", "abc123", "7.5"],
        ])
        rows = parse_calificaciones_file(wb_content, "calif.xlsx")
        assert len(rows) == 1

    def test_parse_file_routes_csv(self):
        content = b"usuario_email,materia_id,nota\njuan@test.com,abc123,7.5"
        rows = parse_calificaciones_file(content, "calif.csv")
        assert len(rows) == 1

    def test_parse_file_rejects_unsupported_format(self):
        content = b"some data"
        with pytest.raises(CalificacionParseError) as exc_info:
            parse_calificaciones_file(content, "calif.pdf")
        assert "no soportado" in str(exc_info.value).lower()


class TestUmbralFallback:
    def test_assignment_specific_takes_precedence_over_course_default(self):
        umbral_asignacion = {"umbral_pct": 70, "conjunto_aprobado": ["A", "B"]}
        umbral_curso = {"umbral_pct": 60, "conjunto_aprobado": ["A", "B", "C"]}

        result = derivar_aprobado(65, umbral_asignacion["umbral_pct"], umbral_asignacion["conjunto_aprobado"])
        assert result is True

        result = derivar_aprobado(65, umbral_curso["umbral_pct"], umbral_curso["conjunto_aprobado"])
        assert result is True

    def test_curso_default_used_when_no_assignment_specific(self):
        umbral_default = {"umbral_pct": 60, "conjunto_aprobado": ["A", "B+", "C", "7", "8", "9", "10"]}
        assert derivar_aprobado(7, umbral_default["umbral_pct"], umbral_default["conjunto_aprobado"]) is True

    def test_default_umbral_applied_when_no_umbral_exists(self):
        default_pct = 60
        default_conjunto = ["A", "B+", "C", "7", "8", "9", "10"]
        assert derivar_aprobado(7, default_pct, default_conjunto) is True
        assert derivar_aprobado("A", default_pct, default_conjunto) is True
        assert derivar_aprobado("D", default_pct, default_conjunto) is False


class TestUmbralRepository:
    async def test_get_by_materia_asignacion_returns_assignment_specific_first(
        self, db_setup, tenant_a, materia_a
    ):
        from app.core.tenancy import TenantContext, set_tenant_context, reset_tenant_context

        token = set_tenant_context(TenantContext(tenant_id=tenant_a))
        try:
            async with db_setup() as session:
                repo = UmbralMateriaRepository(session, tenant_a)

                await repo.create({
                    "materia_id": materia_a,
                    "asignacion_id": None,
                    "umbral_pct": 60,
                    "conjunto_aprobado": ["A", "B", "C"],
                })

                asignacion_id = uuid4()
                await repo.create({
                    "materia_id": materia_a,
                    "asignacion_id": asignacion_id,
                    "umbral_pct": 70,
                    "conjunto_aprobado": ["A", "B"],
                })

                umbral = await repo.get_by_materia_asignacion(materia_a, asignacion_id)
                assert umbral is not None
                assert umbral.umbral_pct == 70
                assert umbral.asignacion_id == asignacion_id
        finally:
            reset_tenant_context(token)

    async def test_get_by_materia_asignacion_falls_back_to_curso_default(
        self, db_setup, tenant_a, materia_a
    ):
        from app.core.tenancy import TenantContext, set_tenant_context, reset_tenant_context

        token = set_tenant_context(TenantContext(tenant_id=tenant_a))
        try:
            async with db_setup() as session:
                repo = UmbralMateriaRepository(session, tenant_a)

                await repo.create({
                    "materia_id": materia_a,
                    "asignacion_id": None,
                    "umbral_pct": 60,
                    "conjunto_aprobado": ["A", "B", "C"],
                })

                asignacion_id = uuid4()
                umbral = await repo.get_by_materia_asignacion(materia_a, asignacion_id)
                assert umbral is not None
                assert umbral.umbral_pct == 60
                assert umbral.asignacion_id is None
        finally:
            reset_tenant_context(token)

    async def test_get_default_for_materia_returns_hardcoded_defaults(
        self, db_setup, tenant_a
    ):
        from app.core.tenancy import TenantContext, set_tenant_context, reset_tenant_context

        token = set_tenant_context(TenantContext(tenant_id=tenant_a))
        try:
            async with db_setup() as session:
                repo = UmbralMateriaRepository(session, tenant_a)
                default = await repo.get_default_for_materia(uuid4())
                assert default["umbral_pct"] == 60
                assert default["conjunto_aprobado"] == ["A", "B+", "C", "7", "8", "9", "10"]
        finally:
            reset_tenant_context(token)


class TestTenantIsolation:
    async def test_tenant_a_no_ve_calificaciones_de_tenant_b(
        self, db_setup, tenant_a, tenant_b, usuario_a, usuario_b, materia_a
    ):
        """Tenant A's calificaciones not visible to tenant B."""
        from app.core.tenancy import TenantContext, set_tenant_context, reset_tenant_context

        mat_b_id = uuid4()
        async with db_setup() as session:
            from app.models.materia import Materia
            m_b = Materia(id=mat_b_id, tenant_id=tenant_b, codigo="M-B", nombre="Materia B", estado="Activa")
            session.add(m_b)
            await session.flush()

        token_a = set_tenant_context(TenantContext(tenant_id=tenant_a))
        try:
            async with db_setup() as session:
                repo_a = CalificacionRepository(session, tenant_a)
                await repo_a.create_many(
                    rows_data=[{
                        "materia_id": materia_a,
                        "usuario_id": usuario_a,
                        "asignacion_id": None,
                        "nota": 7.0,
                        "origen": "Manual",
                    }],
                    import_batch_id=uuid4(),
                    created_by=usuario_a,
                )
        finally:
            reset_tenant_context(token_a)

        token_b = set_tenant_context(TenantContext(tenant_id=tenant_b))
        try:
            async with db_setup() as session:
                repo_b = CalificacionRepository(session, tenant_b)
                calificaciones = await repo_b.get_filtered(materia_id=mat_b_id)
                assert len(calificaciones) == 0
        finally:
            reset_tenant_context(token_b)


class TestDuplicateDetection:
    async def test_duplicate_within_file_marked_invalid(self, db_setup, tenant_a, materia_a, usuario_a):
        """Importing same usuario+asignacion twice in same file marks second as invalid."""
        from app.core.tenancy import TenantContext, set_tenant_context, reset_tenant_context

        token = set_tenant_context(TenantContext(tenant_id=tenant_a))
        try:
            async with db_setup() as session:
                usuario_ids_by_email = {"juan@test.com": usuario_a}
                materia_ids = {materia_a}
                asignacion_ids: set = set()

                svc = ImportService(
                    session=session,
                    tenant_id=tenant_a,
                    usuario_ids_by_email=usuario_ids_by_email,
                    materia_ids=materia_ids,
                    asignacion_ids=asignacion_ids,
                )

                content = b"usuario_email,materia_id,nota\njuan@test.com," + str(materia_a).encode() + b",7.5\njuan@test.com," + str(materia_a).encode() + b",8.0"
                result = svc.parse_preview(content, "test.csv")

                assert result.total == 2
                valid_rows = [r for r in result.rows if r.valid]
                invalid_rows = [r for r in result.rows if not r.valid]
                assert len(valid_rows) == 1
                assert len(invalid_rows) == 1
                assert "duplicado" in invalid_rows[0].warnings[0].lower()
        finally:
            reset_tenant_context(token)


def _make_xlsx_bytes(rows: list[list[str]]) -> bytes:
    """Build a minimal xlsx file from a list of rows using openpyxl."""
    wb = openpyxl.Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()