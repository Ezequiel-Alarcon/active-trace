from __future__ import annotations

import os
from datetime import date
from decimal import Decimal
from uuid import UUID

import pytest
import pytest_asyncio
import sqlalchemy
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.tenancy import TenantContext, reset_tenant_context, set_tenant_context
from app.models.base import Base
from app.models.asignacion import Asignacion, ContextoTipo
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.tenant import Tenant, TenantEstado
from app.models.usuario import Usuario
from app.repositories.usuarios import UsuarioRepository
from app.rbac.models import Rol
from app.schemas.liquidaciones import (
    FacturaCreate,
    FacturaPagoConfirm,
    LiquidacionCalcularRequest,
    LiquidacionCerrarRequest,
    SalarioBaseCreate,
    SalarioPlusCreate,
)
from app.services.liquidaciones import FacturaService, GrillaSalarialService, LiquidacionService

pytestmark = pytest.mark.no_db


@pytest_asyncio.fixture
async def db_factory():
    from app.models import tenant, usuario, asignacion, carrera, cohorte, materia  # noqa: F401
    from app.models import liquidacion as liquidacion_models  # noqa: F401
    from app.rbac import models as rbac_models  # noqa: F401
    from app.auth import models as auth_models  # noqa: F401
    from app.audit import models as audit_models  # noqa: F401

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
        await conn.execute(sqlalchemy.text("""
            INSERT INTO plus_categoria (grupo, descripcion) VALUES
            ('PROG', 'Materias de programacion'),
            ('MAT', 'Materias matematicas'),
            ('IDI', 'Materias de idiomas')
            ON CONFLICT (grupo) DO NOTHING
        """))
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    yield factory
    await engine.dispose()


async def _seed_base(session) -> tuple[UUID, dict[str, UUID], dict[str, UUID]]:
    tenant = Tenant(codigo="LIQ", nombre="Liquidaciones", estado=TenantEstado.ACTIVO)
    session.add(tenant)
    await session.flush()
    roles = {}
    for name in ("PROFESOR", "TUTOR", "COORDINADOR", "NEXO"):
        rol = Rol(tenant_id=tenant.id, nombre=name, descripcion=name)
        session.add(rol)
        await session.flush()
        roles[name] = rol.id
    carrera = Carrera(tenant_id=tenant.id, codigo="CAR", nombre="Carrera")
    session.add(carrera)
    await session.flush()
    cohorte = Cohorte(
        tenant_id=tenant.id,
        carrera_id=carrera.id,
        nombre="2026-A",
        anio=2026,
        vig_desde=date(2026, 1, 1),
    )
    session.add(cohorte)
    materias = {}
    for codigo, plus_grupo in (("PROG1", "PROG"), ("PROG2", "PROG"), ("HIST", None)):
        materia = Materia(
            tenant_id=tenant.id,
            codigo=codigo,
            nombre=codigo,
            plus_grupo=plus_grupo,
        )
        session.add(materia)
        await session.flush()
        materias[codigo] = materia.id
    await session.commit()
    return tenant.id, roles, {"cohorte": cohorte.id, **materias}


async def _usuario(session, tenant_id: UUID, email: str, *, facturante: bool = False) -> Usuario:
    repo = UsuarioRepository(session, tenant_id)
    usuario = await repo.create({
        "tenant_id": tenant_id,
        "nombre": email.split("@")[0],
        "apellidos": "Docente",
        "email": email,
        "dni": email[:3],
        "cuil": email[:4],
        "cbu": "000",
        "facturante": facturante,
    })
    await session.flush()
    return usuario


async def _asignacion(
    session,
    *,
    tenant_id: UUID,
    usuario_id: UUID,
    rol_id: UUID,
    materia_id: UUID,
    cohorte_id: UUID,
    comisiones: list[str],
) -> None:
    session.add(Asignacion(
        tenant_id=tenant_id,
        usuario_id=usuario_id,
        rol_id=rol_id,
        contexto_tipo=ContextoTipo.MATERIA,
        contexto_id=materia_id,
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        comisiones=comisiones,
        desde=date(2026, 1, 1),
    ))
    await session.flush()


@pytest.mark.asyncio
async def test_grilla_selects_current_salary_and_rejects_missing_base(db_factory) -> None:
    async with db_factory() as session:
        tenant_id, roles, ids = await _seed_base(session)
    token = set_tenant_context(TenantContext(tenant_id=tenant_id))
    try:
        async with db_factory() as session:
            svc = GrillaSalarialService(session, tenant_id)
            await svc.create_salario_base(SalarioBaseCreate(
                rol="TUTOR", monto=Decimal("80000"), desde=date(2026, 1, 1), hasta=date(2026, 5, 31)
            ))
            await svc.create_salario_base(SalarioBaseCreate(
                rol="TUTOR", monto=Decimal("90000"), desde=date(2026, 6, 1), hasta=None
            ))
            await session.commit()

        async with db_factory() as session:
            docente = await _usuario(session, tenant_id, "tutor@test.com")
            await _asignacion(
                session,
                tenant_id=tenant_id,
                usuario_id=docente.id,
                rol_id=roles["TUTOR"],
                materia_id=ids["HIST"],
                cohorte_id=ids["cohorte"],
                comisiones=["A"],
            )
            await session.commit()

        async with db_factory() as session:
            result = await LiquidacionService(session, tenant_id).calcular(
                LiquidacionCalcularRequest(cohorte_id=ids["cohorte"], periodo="2026-06")
            )
            assert result.items[0].monto_base == Decimal("90000")

        async with db_factory() as session:
            docente = await _usuario(session, tenant_id, "nexo-sin-base@test.com")
            await _asignacion(
                session,
                tenant_id=tenant_id,
                usuario_id=docente.id,
                rol_id=roles["NEXO"],
                materia_id=ids["HIST"],
                cohorte_id=ids["cohorte"],
                comisiones=["B"],
            )
            await session.commit()

        async with db_factory() as session:
            with pytest.raises(HTTPException) as exc:
                await LiquidacionService(session, tenant_id).calcular(
                    LiquidacionCalcularRequest(cohorte_id=ids["cohorte"], periodo="2026-06")
                )
            assert exc.value.status_code == 409
    finally:
        reset_tenant_context(token)


@pytest.mark.asyncio
async def test_grilla_rejects_overlapping_base_and_plus(db_factory) -> None:
    async with db_factory() as session:
        tenant_id, _roles, _ids = await _seed_base(session)
    token = set_tenant_context(TenantContext(tenant_id=tenant_id))
    try:
        async with db_factory() as session:
            svc = GrillaSalarialService(session, tenant_id)
            await svc.create_salario_base(SalarioBaseCreate(
                rol="PROFESOR", monto=Decimal("100000"), desde=date(2026, 6, 1), hasta=None
            ))
            with pytest.raises(HTTPException) as exc:
                await svc.create_salario_base(SalarioBaseCreate(
                    rol="PROFESOR", monto=Decimal("110000"), desde=date(2026, 7, 1), hasta=None
                ))
            assert exc.value.status_code == 409

            await svc.create_salario_plus(SalarioPlusCreate(
                grupo="PROG", rol="PROFESOR", descripcion="Programacion", monto=Decimal("25000"), desde=date(2026, 6, 1), hasta=None
            ))
            with pytest.raises(HTTPException) as exc:
                await svc.create_salario_plus(SalarioPlusCreate(
                    grupo="PROG", rol="PROFESOR", descripcion="Programacion", monto=Decimal("26000"), desde=date(2026, 8, 1), hasta=None
                ))
            assert exc.value.status_code == 409
    finally:
        reset_tenant_context(token)


@pytest.mark.asyncio
async def test_liquidacion_accumulates_plus_segments_facturantes_and_blocks_closed_recalc(db_factory) -> None:
    async with db_factory() as session:
        tenant_id, roles, ids = await _seed_base(session)
    token = set_tenant_context(TenantContext(tenant_id=tenant_id))
    try:
        async with db_factory() as session:
            grilla = GrillaSalarialService(session, tenant_id)
            for rol in ("PROFESOR", "TUTOR", "NEXO"):
                await grilla.create_salario_base(SalarioBaseCreate(
                    rol=rol, monto=Decimal("100000"), desde=date(2026, 6, 1), hasta=None
                ))
            await grilla.create_salario_plus(SalarioPlusCreate(
                grupo="PROG", rol="PROFESOR", descripcion="Programacion", monto=Decimal("25000"), desde=date(2026, 6, 1), hasta=None
            ))
            await grilla.create_salario_plus(SalarioPlusCreate(
                grupo="PROG", rol="NEXO", descripcion="Programacion", monto=Decimal("10000"), desde=date(2026, 6, 1), hasta=None
            ))
            await session.commit()

        async with db_factory() as session:
            profe = await _usuario(session, tenant_id, "profe@test.com")
            nexo = await _usuario(session, tenant_id, "nexo@test.com")
            factura = await _usuario(session, tenant_id, "factura@test.com", facturante=True)
            await _asignacion(session, tenant_id=tenant_id, usuario_id=profe.id, rol_id=roles["PROFESOR"], materia_id=ids["PROG1"], cohorte_id=ids["cohorte"], comisiones=["A", "B"])
            await _asignacion(session, tenant_id=tenant_id, usuario_id=profe.id, rol_id=roles["PROFESOR"], materia_id=ids["HIST"], cohorte_id=ids["cohorte"], comisiones=["C"])
            await _asignacion(session, tenant_id=tenant_id, usuario_id=nexo.id, rol_id=roles["NEXO"], materia_id=ids["PROG2"], cohorte_id=ids["cohorte"], comisiones=["A"])
            await _asignacion(session, tenant_id=tenant_id, usuario_id=factura.id, rol_id=roles["PROFESOR"], materia_id=ids["PROG1"], cohorte_id=ids["cohorte"], comisiones=["A"])
            await session.commit()

        async with db_factory() as session:
            svc = LiquidacionService(session, tenant_id)
            result = await svc.calcular(LiquidacionCalcularRequest(cohorte_id=ids["cohorte"], periodo="2026-06"))
            profe_row = next(i for i in result.items if i.rol == "PROFESOR" and not i.excluido_por_factura)
            assert profe_row.monto_plus == Decimal("50000")
            assert profe_row.total == Decimal("150000")
            assert any(c["materia_codigo"] == "HIST" and c["plus_grupo"] is None for c in profe_row.comisiones)
            assert result.segmentos.nexo_total == Decimal("110000")
            assert result.kpis.total_sin_factura == Decimal("260000")
            assert result.kpis.total_facturantes == Decimal("125000")

            closed = await svc.cerrar(
                LiquidacionCerrarRequest(cohorte_id=ids["cohorte"], periodo="2026-06", confirmar=True),
                actor_id=profe_row.usuario_id,
            )
            assert closed.filas_afectadas == 3
            with pytest.raises(HTTPException) as exc:
                await svc.calcular(LiquidacionCalcularRequest(cohorte_id=ids["cohorte"], periodo="2026-06"))
            assert exc.value.status_code == 409
    finally:
        reset_tenant_context(token)


@pytest.mark.asyncio
async def test_facturas_flow_filters_confirmation_and_tenant_isolation(db_factory) -> None:
    async with db_factory() as session:
        tenant_id, _roles, _ids = await _seed_base(session)
        other = Tenant(codigo="OTHER", nombre="Other", estado=TenantEstado.ACTIVO)
        session.add(other)
        await session.commit()
        other_id = other.id

    token = set_tenant_context(TenantContext(tenant_id=tenant_id))
    try:
        async with db_factory() as session:
            facturante = await _usuario(session, tenant_id, "facturante@test.com", facturante=True)
            no_facturante = await _usuario(session, tenant_id, "no@test.com")
            service = FacturaService(session, tenant_id)
            created = await service.registrar(FacturaCreate(
                usuario_id=facturante.id,
                periodo="2026-06",
                detalle="Servicios docentes",
                referencia_archivo="facturas/f1.pdf",
                tamano_kb=120,
            ))
            assert created.estado == "Pendiente"

            with pytest.raises(HTTPException) as exc:
                await service.registrar(FacturaCreate(
                    usuario_id=no_facturante.id,
                    periodo="2026-06",
                    detalle="No corresponde",
                    referencia_archivo="facturas/f2.pdf",
                    tamano_kb=100,
                ))
            assert exc.value.status_code == 409

            pending = await service.listar(estado="Pendiente", desde=date(2026, 1, 1), hasta=date(2026, 12, 31))
            assert [f.id for f in pending] == [created.id]

            with pytest.raises(HTTPException) as exc:
                await service.marcar_abonada(created.id, FacturaPagoConfirm(confirmar=False))
            assert exc.value.status_code == 422

            paid = await service.marcar_abonada(created.id, FacturaPagoConfirm(confirmar=True))
            assert paid.estado == "Abonada"
            await session.commit()

        async with db_factory() as session:
            rows = (await session.execute(select(Usuario).where(Usuario.tenant_id == tenant_id))).scalars().all()
            assert rows

        async with db_factory() as session:
            with pytest.raises(HTTPException) as exc:
                await FacturaService(session, other_id).resolver_descarga(created.id)
            assert exc.value.status_code == 404
    finally:
        reset_tenant_context(token)
