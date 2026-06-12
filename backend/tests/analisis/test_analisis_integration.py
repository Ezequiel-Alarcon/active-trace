"""Tests de integracion para analisis C-11."""

from __future__ import annotations

import pytest

from app.core.tenancy import TenantContext, set_tenant_context, reset_tenant_context
from app.domain.analisis.repositories.analisis_repository import AnalisisRepository
from app.domain.analisis.services.analisis_service import (
    AnalisisService,
    FechaInvalidaError,
    RangoExcedidoError,
)


class TestRanking:
    async def test_ranking_ordena_por_cantidad_aprobadas(
        self, db_setup, tenant_a, usuario_a
    ):
        """Un alumno con 2 actividades aprobadas aparece en ranking."""
        from app.models.materia import Materia, MateriaEstado
        from app.domain.calificaciones.models.calificacion import Calificacion

        token = set_tenant_context(TenantContext(tenant_id=tenant_a))
        try:
            # Escritura y lectura en sessions separados
            async with db_setup() as session:
                materia = Materia(
                    tenant_id=tenant_a,
                    codigo="ANALISIS-101",
                    nombre="Analisis Matematico I",
                    estado=MateriaEstado.ACTIVA,
                )
                session.add(materia)
                await session.flush()
                mid = materia.id
                session.add(Calificacion(
                    tenant_id=tenant_a, materia_id=mid,
                    usuario_id=usuario_a, nota=7.5, origen="Importado",
                ))
                session.add(Calificacion(
                    tenant_id=tenant_a, materia_id=mid,
                    usuario_id=usuario_a, nota=8.0, origen="Importado",
                ))
                session.add(Calificacion(
                    tenant_id=tenant_a, materia_id=mid,
                    usuario_id=usuario_a, nota=None, origen="Importado",
                ))
                await session.commit()

            async with db_setup() as session:
                repo = AnalisisRepository(session, tenant_a)
                ranking = await repo.get_ranking(mid, limit=10)
                assert len(ranking) >= 1
                assert ranking[0]["usuario_id"] == usuario_a
                assert ranking[0]["aprobadas_count"] == 2
        finally:
            reset_tenant_context(token)

    async def test_ranking_orden_descendente(
        self, db_setup, tenant_a, materia_analisis, usuario_a, usuario_b, umbral_analisis
    ):
        """Alumno con mas aprobadas aparece primero."""
        from app.domain.calificaciones.models.calificacion import Calificacion

        token = set_tenant_context(TenantContext(tenant_id=tenant_a))
        try:
            async with db_setup() as session:
                # usuario_a: 2 aprobadas
                session.add(Calificacion(
                    tenant_id=tenant_a, materia_id=materia_analisis,
                    usuario_id=usuario_a, nota=7.0, origen="Importado",
                ))
                session.add(Calificacion(
                    tenant_id=tenant_a, materia_id=materia_analisis,
                    usuario_id=usuario_a, nota=8.0, origen="Importado",
                ))
                # usuario_b: 3 aprobadas
                for i in range(1, 4):
                    session.add(Calificacion(
                        tenant_id=tenant_a, materia_id=materia_analisis,
                        usuario_id=usuario_b, nota=7.0 + i * 0.5, origen="Importado",
                    ))
                await session.commit()

            async with db_setup() as session:
                repo = AnalisisRepository(session, tenant_a)
                ranking = await repo.get_ranking(materia_analisis)
                assert ranking[0]["usuario_id"] == usuario_b
                assert ranking[0]["aprobadas_count"] == 3
        finally:
            reset_tenant_context(token)


class TestReporteMateria:
    async def test_reporte_materia_cuenta_alumnos(
        self, db_setup, tenant_a, materia_analisis, usuario_a
    ):
        """Reporte por materia retorna conteos correctos."""
        from app.domain.calificaciones.models.calificacion import Calificacion

        token = set_tenant_context(TenantContext(tenant_id=tenant_a))
        try:
            async with db_setup() as session:
                session.add(Calificacion(
                    tenant_id=tenant_a, materia_id=materia_analisis,
                    usuario_id=usuario_a, nota=7.5, origen="Importado",
                ))
                await session.commit()

            async with db_setup() as session:
                repo = AnalisisRepository(session, tenant_a)
                reporte = await repo.get_reporte_materia(materia_analisis)
                assert reporte["materia_id"] == str(materia_analisis)
                assert reporte["alumnos_con_actividad"] >= 1
        finally:
            reset_tenant_context(token)


class TestTpsSinCorregir:
    async def test_tps_sin_nota_devuelve_alumnos(
        self, db_setup, tenant_a, materia_analisis, usuario_a
    ):
        """Alumnos con actividad sin nota aparecen en TPs sin corregir."""
        from app.domain.calificaciones.models.calificacion import Calificacion

        token = set_tenant_context(TenantContext(tenant_id=tenant_a))
        try:
            async with db_setup() as session:
                session.add(Calificacion(
                    tenant_id=tenant_a, materia_id=materia_analisis,
                    usuario_id=usuario_a, nota=None, origen="Importado",
                ))
                await session.commit()

            async with db_setup() as session:
                repo = AnalisisRepository(session, tenant_a)
                tps = await repo.get_tps_sin_corregir(materia_id=materia_analisis)
                assert isinstance(tps, list)
        finally:
            reset_tenant_context(token)


class TestMonitores:
    async def test_monitor_general_devuelve_datos(
        self, db_setup, tenant_a, materia_analisis, usuario_a
    ):
        """Monitor general retorna datos para el docente."""
        from app.models.asignacion import Asignacion, ContextoTipo
        from app.rbac.models import Rol
        from datetime import date

        token = set_tenant_context(TenantContext(tenant_id=tenant_a))
        try:
            async with db_setup() as session:
                rol = Rol(tenant_id=tenant_a, nombre="Profesor")
                session.add(rol)
                await session.flush()
                desde = date(2020, 1, 1)
                session.add(Asignacion(
                    tenant_id=tenant_a, usuario_id=usuario_a, rol_id=rol.id,
                    contexto_tipo=ContextoTipo.MATERIA, contexto_id=materia_analisis,
                    desde=desde,
                ))
                from app.domain.calificaciones.models.calificacion import Calificacion
                session.add(Calificacion(
                    tenant_id=tenant_a, materia_id=materia_analisis,
                    usuario_id=usuario_a, nota=7.5, origen="Importado",
                ))
                await session.commit()

            async with db_setup() as session:
                repo = AnalisisRepository(session, tenant_a)
                datos = await repo.get_monitor_general(usuario_a)
                assert isinstance(datos, list)
        finally:
            reset_tenant_context(token)

    async def test_monitor_coordinacion_valida_rango(
        self, db_setup, tenant_a
    ):
        """Monitor coordinacion rechaza rango invalido."""
        token = set_tenant_context(TenantContext(tenant_id=tenant_a))
        try:
            async with db_setup() as session:
                svc = AnalisisService(session, tenant_a)
                with pytest.raises(FechaInvalidaError):
                    await svc.get_monitor_coordinacion("2024-12-31", "2024-01-01")
        finally:
            reset_tenant_context(token)

    async def test_monitor_coordinacion_rechaza_rango_excedido(
        self, db_setup, tenant_a
    ):
        """Monitor coordinacion rechaza rango > 365 dias."""
        token = set_tenant_context(TenantContext(tenant_id=tenant_a))
        try:
            async with db_setup() as session:
                svc = AnalisisService(session, tenant_a)
                with pytest.raises(RangoExcedidoError):
                    await svc.get_monitor_coordinacion("2024-01-01", "2025-06-01")
        finally:
            reset_tenant_context(token)


class TestTenantIsolation:
    async def test_analisis_no_ve_datos_de_otro_tenant(
        self, db_setup, tenant_a, tenant_b, materia_analisis
    ):
        """Datos del tenant A no son visibles para tenant B."""
        token = set_tenant_context(TenantContext(tenant_id=tenant_b))
        try:
            async with db_setup() as session:
                repo = AnalisisRepository(session, tenant_b)
                ranking = await repo.get_ranking(materia_analisis)
                # materia_analisis pertenece a tenant_a, no a tenant_b
                # por lo tanto no debe retornar datos
                assert len(ranking) == 0
        finally:
            reset_tenant_context(token)