from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.core.tenancy import TenantContext, reset_tenant_context, set_tenant_context
from app.models.tenant import Tenant, TenantEstado
from app.schemas.avisos import AvisoCreate, AvisoUpdate
from app.services.avisos import AvisoService
from tests.avisos.conftest import (
    _create_tenant,
    _create_user_and_session,
    _seed_rbac,
)

pytestmark = [pytest.mark.asyncio, pytest.mark.no_db]

# ── Helpers ────────────────────────────────────────────────────────────


def _future_window(days_start=1, days_end=30):
    now = datetime.now(timezone.utc)
    return now - timedelta(days=days_start), now + timedelta(days=days_end)


async def _setup_tenant(db_setup) -> tuple:
    async with db_setup() as session:
        role_ids = await _seed_rbac(session)
        tenant = await _create_tenant(session)
        await session.commit()
        tid = tenant.id
    return tid, role_ids


async def _setup_admin(db_setup, tid, role_ids):
    async with db_setup() as session:
        uid, _, _ = await _create_user_and_session(session, tid, rol_id=role_ids["ADMIN"])
        await session.commit()
    return uid


# ═══════════════════════════════════════════════════════════════════════
# 1. CRUD
# ═══════════════════════════════════════════════════════════════════════

async def test_create_aviso_global_succeeds(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        inicio, fin = _future_window()
        async with db_setup() as session:
            svc = AvisoService(session, tid)
            aviso = await svc.create(AvisoCreate(
                titulo="Feriado 25 de Mayo",
                cuerpo="El 25 de mayo es feriado nacional",
                alcance="Global",
                severidad="Info",
                inicio_en=inicio,
                fin_en=fin,
                requiere_ack=False,
            ))
            await session.commit()
            assert aviso.id is not None
            assert aviso.tenant_id == tid
            assert aviso.titulo == "Feriado 25 de Mayo"
            assert aviso.alcance == "Global"
            assert aviso.severidad == "Info"
            assert aviso.activo is True
            assert aviso.requiere_ack is False
            assert aviso.orden == 0
    finally:
        reset_tenant_context(token)


async def test_create_aviso_por_rol_con_severidad(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        inicio, fin = _future_window()
        async with db_setup() as session:
            svc = AvisoService(session, tid)
            aviso = await svc.create(AvisoCreate(
                titulo="Reunion urgente",
                cuerpo="Reunion obligatoria para profesores",
                alcance="PorRol",
                severidad="Crítico",
                rol_destino="PROFESOR",
                inicio_en=inicio,
                fin_en=fin,
                requiere_ack=True,
            ))
            await session.commit()
            assert aviso.id is not None
            assert aviso.alcance == "PorRol"
            assert aviso.severidad == "Crítico"
            assert aviso.rol_destino == "PROFESOR"
            assert aviso.requiere_ack is True
    finally:
        reset_tenant_context(token)


async def test_get_aviso_by_id_succeeds(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    inicio, fin = _future_window()
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AvisoService(session, tid)
            created = await svc.create(AvisoCreate(
                titulo="Test",
                cuerpo="Body",
                alcance="Global",
                inicio_en=inicio,
                fin_en=fin,
            ))
            await session.commit()
            created_id = created.id

        async with db_setup() as session:
            svc = AvisoService(session, tid)
            retrieved = await svc.get(created_id)
            assert retrieved.id == created_id
            assert retrieved.titulo == "Test"
    finally:
        reset_tenant_context(token)


async def test_get_aviso_not_found_raises_404(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AvisoService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.get(uuid4())
            assert exc.value.status_code == 404
    finally:
        reset_tenant_context(token)


async def test_update_aviso_titulo(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    inicio, fin = _future_window()
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AvisoService(session, tid)
            created = await svc.create(AvisoCreate(
                titulo="Old Title",
                cuerpo="Body",
                alcance="Global",
                inicio_en=inicio,
                fin_en=fin,
            ))
            await session.commit()
            created_id = created.id

        async with db_setup() as session:
            svc = AvisoService(session, tid)
            updated = await svc.update(created_id, AvisoUpdate(titulo="New Title"))
            await session.commit()
            assert updated.titulo == "New Title"
            assert updated.cuerpo == "Body"
    finally:
        reset_tenant_context(token)


async def test_soft_delete_aviso(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    inicio, fin = _future_window()
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AvisoService(session, tid)
            created = await svc.create(AvisoCreate(
                titulo="To Delete",
                cuerpo="Body",
                alcance="Global",
                inicio_en=inicio,
                fin_en=fin,
            ))
            await session.commit()
            created_id = created.id

        async with db_setup() as session:
            svc = AvisoService(session, tid)
            await svc.delete(created_id)
            await session.commit()

        async with db_setup() as session:
            svc = AvisoService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.get(created_id)
            assert exc.value.status_code == 404
    finally:
        reset_tenant_context(token)


async def test_list_all_avisos_paginated(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    inicio, fin = _future_window()
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AvisoService(session, tid)
            for i in range(3):
                await svc.create(AvisoCreate(
                    titulo=f"Aviso {i}",
                    cuerpo="Body",
                    alcance="Global",
                    inicio_en=inicio,
                    fin_en=fin,
                ))
            await session.commit()

        async with db_setup() as session:
            svc = AvisoService(session, tid)
            items, total = await svc.list_all(page=1, per_page=2)
            assert len(items) == 2
            assert total == 3
    finally:
        reset_tenant_context(token)


async def test_list_all_filtered_by_alcance(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    inicio, fin = _future_window()
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AvisoService(session, tid)
            await svc.create(AvisoCreate(
                titulo="Global", cuerpo="Body", alcance="Global", inicio_en=inicio, fin_en=fin,
            ))
            await svc.create(AvisoCreate(
                titulo="PorRol", cuerpo="Body", alcance="PorRol", inicio_en=inicio, fin_en=fin,
            ))
            await session.commit()

        async with db_setup() as session:
            svc = AvisoService(session, tid)
            items_global, total_global = await svc.list_all(alcance="Global")
            assert total_global == 1
            assert items_global[0].titulo == "Global"

            items_rol, total_rol = await svc.list_all(alcance="PorRol")
            assert total_rol == 1
            assert items_rol[0].titulo == "PorRol"
    finally:
        reset_tenant_context(token)


async def test_multi_tenant_isolation(db_setup) -> None:
    async with db_setup() as session:
        await _seed_rbac(session)
        t_a = Tenant(codigo="T-A", nombre="Tenant A", estado=TenantEstado.ACTIVO)
        session.add(t_a)
        await session.flush()
        t_b = Tenant(codigo="T-B", nombre="Tenant B", estado=TenantEstado.ACTIVO)
        session.add(t_b)
        await session.commit()
        tid_a, tid_b = t_a.id, t_b.id

    inicio, fin = _future_window()
    token_a = set_tenant_context(TenantContext(tenant_id=tid_a))
    try:
        async with db_setup() as session:
            svc = AvisoService(session, tid_a)
            await svc.create(AvisoCreate(
                titulo="A-Only", cuerpo="Body", alcance="Global", inicio_en=inicio, fin_en=fin,
            ))
            await session.commit()
    finally:
        reset_tenant_context(token_a)

    token_b = set_tenant_context(TenantContext(tenant_id=tid_b))
    try:
        async with db_setup() as session:
            svc = AvisoService(session, tid_b)
            items, total = await svc.list_all()
            assert total == 0
    finally:
        reset_tenant_context(token_b)

    token_a = set_tenant_context(TenantContext(tenant_id=tid_a))
    try:
        async with db_setup() as session:
            svc = AvisoService(session, tid_a)
            items, total = await svc.list_all()
            assert total == 1
            assert items[0].titulo == "A-Only"
    finally:
        reset_tenant_context(token_a)


# ═══════════════════════════════════════════════════════════════════════
# 2. Visibility
# ═══════════════════════════════════════════════════════════════════════

async def test_list_visible_includes_global_aviso(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    inicio, fin = _future_window()
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AvisoService(session, tid)
            await svc.create(AvisoCreate(
                titulo="Global Notice",
                cuerpo="For everyone",
                alcance="Global",
                inicio_en=inicio,
                fin_en=fin,
            ))
            await session.commit()

        async with db_setup() as session:
            svc = AvisoService(session, tid)
            visible = await svc.list_visible(
                user_id=uuid4(),
                user_roles=["ALUMNO"],
            )
            assert len(visible) == 1
            assert visible[0].titulo == "Global Notice"
    finally:
        reset_tenant_context(token)


async def test_list_visible_excludes_expired_aviso(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    now = datetime.now(timezone.utc)
    past_start = now - timedelta(days=10)
    past_end = now - timedelta(days=1)
    future_end = now + timedelta(days=30)
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AvisoService(session, tid)
            await svc.create(AvisoCreate(
                titulo="Expired",
                cuerpo="Old",
                alcance="Global",
                inicio_en=past_start,
                fin_en=past_end,
            ))
            await svc.create(AvisoCreate(
                titulo="Current",
                cuerpo="Now",
                alcance="Global",
                inicio_en=past_start,
                fin_en=future_end,
            ))
            await session.commit()

        async with db_setup() as session:
            svc = AvisoService(session, tid)
            visible = await svc.list_visible(user_id=uuid4(), user_roles=["ALUMNO"])
            titulos = {v.titulo for v in visible}
            assert "Current" in titulos
            assert "Expired" not in titulos
            assert len(visible) == 1
    finally:
        reset_tenant_context(token)


async def test_list_visible_excludes_future_aviso(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    now = datetime.now(timezone.utc)
    future_start = now + timedelta(days=5)
    future_end = now + timedelta(days=30)
    current_start = now - timedelta(days=1)
    current_end = now + timedelta(days=30)
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AvisoService(session, tid)
            await svc.create(AvisoCreate(
                titulo="Future",
                cuerpo="Not yet",
                alcance="Global",
                inicio_en=future_start,
                fin_en=future_end,
            ))
            await svc.create(AvisoCreate(
                titulo="Current",
                cuerpo="Now",
                alcance="Global",
                inicio_en=current_start,
                fin_en=current_end,
            ))
            await session.commit()

        async with db_setup() as session:
            svc = AvisoService(session, tid)
            visible = await svc.list_visible(user_id=uuid4(), user_roles=["ALUMNO"])
            titulos = {v.titulo for v in visible}
            assert "Current" in titulos
            assert "Future" not in titulos
    finally:
        reset_tenant_context(token)


async def test_list_visible_excludes_inactive_aviso(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    inicio, fin = _future_window()
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AvisoService(session, tid)
            await svc.create(AvisoCreate(
                titulo="Inactive",
                cuerpo="Off",
                alcance="Global",
                inicio_en=inicio,
                fin_en=fin,
                activo=False,
            ))
            await svc.create(AvisoCreate(
                titulo="Active",
                cuerpo="On",
                alcance="Global",
                inicio_en=inicio,
                fin_en=fin,
                activo=True,
            ))
            await session.commit()

        async with db_setup() as session:
            svc = AvisoService(session, tid)
            visible = await svc.list_visible(user_id=uuid4(), user_roles=["ALUMNO"])
            titulos = {v.titulo for v in visible}
            assert "Active" in titulos
            assert "Inactive" not in titulos
    finally:
        reset_tenant_context(token)


async def test_list_visible_por_rol_matches_user_role(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    inicio, fin = _future_window()
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AvisoService(session, tid)
            await svc.create(AvisoCreate(
                titulo="For Profesores",
                cuerpo="Teachers only",
                alcance="PorRol",
                rol_destino="PROFESOR",
                inicio_en=inicio,
                fin_en=fin,
            ))
            await session.commit()

        async with db_setup() as session:
            svc = AvisoService(session, tid)
            visible_prof = await svc.list_visible(
                user_id=uuid4(), user_roles=["PROFESOR"],
            )
            assert len(visible_prof) == 1
            assert visible_prof[0].titulo == "For Profesores"

            visible_alumno = await svc.list_visible(
                user_id=uuid4(), user_roles=["ALUMNO"],
            )
            assert len(visible_alumno) == 0
    finally:
        reset_tenant_context(token)


async def test_list_visible_por_rol_null_rol_destino_visible_to_all(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    inicio, fin = _future_window()
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AvisoService(session, tid)
            await svc.create(AvisoCreate(
                titulo="All Roles",
                cuerpo="Null destino visible to all",
                alcance="PorRol",
                inicio_en=inicio,
                fin_en=fin,
            ))
            await session.commit()

        async with db_setup() as session:
            svc = AvisoService(session, tid)
            visible = await svc.list_visible(
                user_id=uuid4(), user_roles=["ALUMNO"],
            )
            assert len(visible) == 1
            assert visible[0].titulo == "All Roles"
    finally:
        reset_tenant_context(token)


async def test_list_visible_por_materia_matches_user_materias(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    inicio, fin = _future_window()
    materia_a, materia_b = uuid4(), uuid4()
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AvisoService(session, tid)
            await svc.create(AvisoCreate(
                titulo="Materia A Notice",
                cuerpo="For materia A",
                alcance="PorMateria",
                materia_id=materia_a,
                inicio_en=inicio,
                fin_en=fin,
            ))
            await svc.create(AvisoCreate(
                titulo="Materia B Notice",
                cuerpo="For materia B",
                alcance="PorMateria",
                materia_id=materia_b,
                inicio_en=inicio,
                fin_en=fin,
            ))
            await session.commit()

        async with db_setup() as session:
            svc = AvisoService(session, tid)
            visible = await svc.list_visible(
                user_id=uuid4(), user_roles=["PROFESOR"],
                materia_ids=[materia_a],
            )
            titulos = {v.titulo for v in visible}
            assert "Materia A Notice" in titulos
            assert "Materia B Notice" not in titulos
    finally:
        reset_tenant_context(token)


async def test_list_visible_por_cohorte_matches_user_cohortes(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    inicio, fin = _future_window()
    cohorte_x, cohorte_y = uuid4(), uuid4()
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AvisoService(session, tid)
            await svc.create(AvisoCreate(
                titulo="Cohorte X Notice",
                cuerpo="For cohorte X",
                alcance="PorCohorte",
                cohorte_id=cohorte_x,
                inicio_en=inicio,
                fin_en=fin,
            ))
            await session.commit()

        async with db_setup() as session:
            svc = AvisoService(session, tid)
            visible = await svc.list_visible(
                user_id=uuid4(), user_roles=["ALUMNO"],
                cohorte_ids=[cohorte_x],
            )
            assert len(visible) == 1
            assert visible[0].titulo == "Cohorte X Notice"

            visible_no_match = await svc.list_visible(
                user_id=uuid4(), user_roles=["ALUMNO"],
                cohorte_ids=[cohorte_y],
            )
            assert len(visible_no_match) == 0
    finally:
        reset_tenant_context(token)


async def test_list_visible_sorted_by_orden_then_created_at(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    inicio, fin = _future_window()
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AvisoService(session, tid)
            await svc.create(AvisoCreate(
                titulo="Priority 1", cuerpo="A", alcance="Global",
                inicio_en=inicio, fin_en=fin, orden=1,
            ))
            await session.commit()

        async with db_setup() as session:
            svc = AvisoService(session, tid)
            await svc.create(AvisoCreate(
                titulo="Priority 2", cuerpo="B", alcance="Global",
                inicio_en=inicio, fin_en=fin, orden=2,
            ))
            await session.commit()

        async with db_setup() as session:
            svc = AvisoService(session, tid)
            visible = await svc.list_visible(user_id=uuid4(), user_roles=["ALUMNO"])
            assert len(visible) == 2
            assert visible[0].titulo == "Priority 1"
            assert visible[1].titulo == "Priority 2"
    finally:
        reset_tenant_context(token)


# ═══════════════════════════════════════════════════════════════════════
# 3. Acknowledgment
# ═══════════════════════════════════════════════════════════════════════

async def test_acknowledge_aviso_succeeds(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    inicio, fin = _future_window()
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AvisoService(session, tid)
            aviso = await svc.create(AvisoCreate(
                titulo="Must Acknowledge",
                cuerpo="Please confirm",
                alcance="Global",
                inicio_en=inicio,
                fin_en=fin,
                requiere_ack=True,
            ))
            await session.commit()
            aviso_id = aviso.id

        user_id = uuid4()
        async with db_setup() as session:
            svc = AvisoService(session, tid)
            await svc.acknowledge(aviso_id, user_id)
            await session.commit()

        async with db_setup() as session:
            svc = AvisoService(session, tid)
            status = await svc.get_acknowledgment_status(aviso_id, user_id)
            assert status.total == 1
            assert status.user_acknowledged is True
            assert status.requiere_ack is True
    finally:
        reset_tenant_context(token)


async def test_acknowledge_duplicate_raises_409(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    inicio, fin = _future_window()
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AvisoService(session, tid)
            aviso = await svc.create(AvisoCreate(
                titulo="Dup Test",
                cuerpo="No double ack",
                alcance="Global",
                inicio_en=inicio,
                fin_en=fin,
                requiere_ack=True,
            ))
            await session.commit()
            aviso_id = aviso.id

        user_id = uuid4()
        async with db_setup() as session:
            svc = AvisoService(session, tid)
            await svc.acknowledge(aviso_id, user_id)
            await session.commit()

        async with db_setup() as session:
            svc = AvisoService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.acknowledge(aviso_id, user_id)
            assert exc.value.status_code == 409
            assert "Ya confirmó" in exc.value.detail
    finally:
        reset_tenant_context(token)


async def test_acknowledge_non_ack_aviso_raises_400(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    inicio, fin = _future_window()
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AvisoService(session, tid)
            aviso = await svc.create(AvisoCreate(
                titulo="No Ack Needed",
                cuerpo="Read only",
                alcance="Global",
                inicio_en=inicio,
                fin_en=fin,
                requiere_ack=False,
            ))
            await session.commit()
            aviso_id = aviso.id

        async with db_setup() as session:
            svc = AvisoService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.acknowledge(aviso_id, uuid4())
            assert exc.value.status_code == 400
            assert "no requiere" in exc.value.detail
    finally:
        reset_tenant_context(token)


async def test_acknowledgment_status_without_user_ack(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    inicio, fin = _future_window()
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AvisoService(session, tid)
            aviso = await svc.create(AvisoCreate(
                titulo="Count Test",
                cuerpo="Status check",
                alcance="Global",
                inicio_en=inicio,
                fin_en=fin,
                requiere_ack=True,
            ))
            await session.commit()
            aviso_id = aviso.id

        user_a, user_b = uuid4(), uuid4()
        async with db_setup() as session:
            svc = AvisoService(session, tid)
            await svc.acknowledge(aviso_id, user_a)
            await svc.acknowledge(aviso_id, user_b)
            await session.commit()

        async with db_setup() as session:
            svc = AvisoService(session, tid)
            status = await svc.get_acknowledgment_status(aviso_id, user_a)
            assert status.total == 2
            assert status.user_acknowledged is True
            assert status.requiere_ack is True

            user_c = uuid4()
            status_c = await svc.get_acknowledgment_status(aviso_id, user_c)
            assert status_c.total == 2
            assert status_c.user_acknowledged is False
            assert status_c.requiere_ack is True
    finally:
        reset_tenant_context(token)


async def test_acknowledgment_status_non_ack_aviso(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    inicio, fin = _future_window()
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = AvisoService(session, tid)
            aviso = await svc.create(AvisoCreate(
                titulo="No Ack",
                cuerpo="No confirmation needed",
                alcance="Global",
                inicio_en=inicio,
                fin_en=fin,
                requiere_ack=False,
            ))
            await session.commit()
            aviso_id = aviso.id

        async with db_setup() as session:
            svc = AvisoService(session, tid)
            status = await svc.get_acknowledgment_status(aviso_id, uuid4())
            assert status.total == 0
            assert status.user_acknowledged is False
            assert status.requiere_ack is False
    finally:
        reset_tenant_context(token)
