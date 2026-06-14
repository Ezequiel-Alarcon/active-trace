from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.core.tenancy import TenantContext, reset_tenant_context, set_tenant_context
from app.schemas.tareas import TareaCreate, TareaUpdate, ComentarioCreate
from app.services.tareas import TareaService
from tests.tareas.conftest import (
    _create_tenant,
    _create_user_and_session,
    _seed_rbac,
)

pytestmark = [pytest.mark.asyncio, pytest.mark.no_db]


async def _setup_tenant(db_setup) -> tuple:
    async with db_setup() as session:
        role_ids = await _seed_rbac(session)
        tenant = await _create_tenant(session)
        await session.commit()
        tid = tenant.id
    return tid, role_ids


async def _setup_user(db_setup, tid, role_ids, rol_name="COORDINADOR"):
    async with db_setup() as session:
        uid, _, _ = await _create_user_and_session(session, tid, rol_id=role_ids[rol_name])
        await session.commit()
    return uid


async def _crear_tarea(session, tid, asignado_a, descripcion="Test tarea", **kwargs):
    svc = TareaService(session, tid)
    return await svc.create(TareaCreate(asignado_a=asignado_a, descripcion=descripcion, **kwargs),
                            user_id=kwargs.pop("_user_id", asignado_a),
                            roles=kwargs.pop("_roles", ["PROFESOR"]))


# ═══════════════════════════════════════════════════════════════════════
# 1. CRUD — Create
# ═══════════════════════════════════════════════════════════════════════

async def test_crear_tarea_coordinador(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    coord_id = await _setup_user(db_setup, tid, role_ids, "COORDINADOR")
    docente_id = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = TareaService(session, tid)
            tarea = await svc.create(TareaCreate(
                asignado_a=docente_id,
                descripcion="Revisar planificacion",
            ), user_id=coord_id, roles=["COORDINADOR"])
            await session.commit()
            assert tarea.id is not None
            assert tarea.tenant_id == tid
            assert tarea.asignado_por == coord_id
            assert tarea.asignado_a == docente_id
            assert tarea.descripcion == "Revisar planificacion"
            assert tarea.estado == "Pendiente"
            assert tarea.materia_id is None
            assert tarea.contexto_id is None
    finally:
        reset_tenant_context(token)


async def test_crear_tarea_profesor_propia(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    prof_id = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = TareaService(session, tid)
            tarea = await svc.create(TareaCreate(
                asignado_a=prof_id,
                descripcion="Preparar examen",
            ), user_id=prof_id, roles=["PROFESOR"])
            await session.commit()
            assert tarea.asignado_por == prof_id
            assert tarea.asignado_a == prof_id
    finally:
        reset_tenant_context(token)


async def test_crear_tarea_profesor_a_otro_raise_403(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    prof_id = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    otro_id = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = TareaService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.create(TareaCreate(asignado_a=otro_id, descripcion="No deberia poder"),
                                 user_id=prof_id, roles=["PROFESOR"])
            assert exc.value.status_code == 403
    finally:
        reset_tenant_context(token)


async def test_crear_tarea_sin_descripcion_raise_422(db_setup) -> None:
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        TareaCreate(asignado_a=uuid4())


# ═══════════════════════════════════════════════════════════════════════
# 2. CRUD — Read
# ═══════════════════════════════════════════════════════════════════════

async def test_leer_tarea_profesor_propia(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    prof_id = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = TareaService(session, tid)
            tarea = await svc.create(TareaCreate(asignado_a=prof_id, descripcion="Test"),
                                     user_id=prof_id, roles=["PROFESOR"])
            await session.commit()
            tarea_id = tarea.id

        async with db_setup() as session:
            svc = TareaService(session, tid)
            result = await svc.get(tarea_id, user_id=prof_id, roles=["PROFESOR"])
            assert result.id == tarea_id
    finally:
        reset_tenant_context(token)


async def test_leer_tarea_coordinador_ve_todas(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    coord_id = await _setup_user(db_setup, tid, role_ids, "COORDINADOR")
    prof_id = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = TareaService(session, tid)
            tarea = await svc.create(TareaCreate(asignado_a=prof_id, descripcion="Test"),
                                     user_id=coord_id, roles=["COORDINADOR"])
            await session.commit()
            tarea_id = tarea.id

        async with db_setup() as session:
            svc = TareaService(session, tid)
            result = await svc.get(tarea_id, user_id=coord_id, roles=["COORDINADOR"])
            assert result.id == tarea_id
            assert result.asignado_a == prof_id
    finally:
        reset_tenant_context(token)


async def test_leer_tarea_profesor_ajena_raise_404(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    prof_a = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    prof_b = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = TareaService(session, tid)
            tarea = await svc.create(TareaCreate(asignado_a=prof_a, descripcion="Test"),
                                     user_id=prof_a, roles=["PROFESOR"])
            await session.commit()
            tarea_id = tarea.id

        async with db_setup() as session:
            svc = TareaService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.get(tarea_id, user_id=prof_b, roles=["PROFESOR"])
            assert exc.value.status_code == 404
    finally:
        reset_tenant_context(token)


async def test_leer_tarea_no_existe_raise_404(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    coord_id = await _setup_user(db_setup, tid, role_ids, "COORDINADOR")
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = TareaService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.get(uuid4(), user_id=coord_id, roles=["COORDINADOR"])
            assert exc.value.status_code == 404
    finally:
        reset_tenant_context(token)


# ═══════════════════════════════════════════════════════════════════════
# 3. CRUD — Update estado
# ═══════════════════════════════════════════════════════════════════════

async def test_actualizar_estado_a_en_progreso(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    prof_id = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = TareaService(session, tid)
            tarea = await svc.create(TareaCreate(asignado_a=prof_id, descripcion="Test"),
                                     user_id=prof_id, roles=["PROFESOR"])
            await session.commit()
            tarea_id = tarea.id

        async with db_setup() as session:
            svc = TareaService(session, tid)
            updated = await svc.update(tarea_id, TareaUpdate(estado="En progreso"),
                                       user_id=prof_id, roles=["PROFESOR"])
            await session.commit()
            assert updated.estado == "En progreso"
    finally:
        reset_tenant_context(token)


async def test_actualizar_estado_a_resuelta(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    prof_id = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = TareaService(session, tid)
            tarea = await svc.create(TareaCreate(asignado_a=prof_id, descripcion="Test"),
                                     user_id=prof_id, roles=["PROFESOR"])
            await session.commit()
            tarea_id = tarea.id

        async with db_setup() as session:
            svc = TareaService(session, tid)
            await svc.update(tarea_id, TareaUpdate(estado="En progreso"),
                             user_id=prof_id, roles=["PROFESOR"])
            await session.commit()

        async with db_setup() as session:
            svc = TareaService(session, tid)
            updated = await svc.update(tarea_id, TareaUpdate(estado="Resuelta"),
                                       user_id=prof_id, roles=["PROFESOR"])
            await session.commit()
            assert updated.estado == "Resuelta"
    finally:
        reset_tenant_context(token)


async def test_actualizar_estado_coordinador_cualquiera(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    coord_id = await _setup_user(db_setup, tid, role_ids, "COORDINADOR")
    prof_id = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = TareaService(session, tid)
            tarea = await svc.create(TareaCreate(asignado_a=prof_id, descripcion="Test"),
                                     user_id=coord_id, roles=["COORDINADOR"])
            await session.commit()
            tarea_id = tarea.id

        async with db_setup() as session:
            svc = TareaService(session, tid)
            updated = await svc.update(tarea_id, TareaUpdate(estado="Cancelada"),
                                       user_id=coord_id, roles=["COORDINADOR"])
            await session.commit()
            assert updated.estado == "Cancelada"
    finally:
        reset_tenant_context(token)


async def test_actualizar_estado_profesor_ajeno_raise_404(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    prof_a = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    prof_b = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = TareaService(session, tid)
            tarea = await svc.create(TareaCreate(asignado_a=prof_a, descripcion="Test"),
                                     user_id=prof_a, roles=["PROFESOR"])
            await session.commit()
            tarea_id = tarea.id

        async with db_setup() as session:
            svc = TareaService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.update(tarea_id, TareaUpdate(estado="En progreso"),
                                 user_id=prof_b, roles=["PROFESOR"])
            assert exc.value.status_code == 404
    finally:
        reset_tenant_context(token)


async def test_transicion_invalida_raise_400(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    prof_id = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = TareaService(session, tid)
            tarea = await svc.create(TareaCreate(asignado_a=prof_id, descripcion="Test"),
                                     user_id=prof_id, roles=["PROFESOR"])
            await session.commit()
            tarea_id = tarea.id

        async with db_setup() as session:
            svc = TareaService(session, tid)
            await svc.update(tarea_id, TareaUpdate(estado="En progreso"),
                             user_id=prof_id, roles=["PROFESOR"])
            await session.commit()

        async with db_setup() as session:
            svc = TareaService(session, tid)
            await svc.update(tarea_id, TareaUpdate(estado="Resuelta"),
                             user_id=prof_id, roles=["PROFESOR"])
            await session.commit()

        async with db_setup() as session:
            svc = TareaService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.update(tarea_id, TareaUpdate(estado="Pendiente"),
                                 user_id=prof_id, roles=["PROFESOR"])
            assert exc.value.status_code == 400
    finally:
        reset_tenant_context(token)


# ═══════════════════════════════════════════════════════════════════════
# 4. CRUD — Soft delete
# ═══════════════════════════════════════════════════════════════════════

async def test_eliminar_tarea_coordinador(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    coord_id = await _setup_user(db_setup, tid, role_ids, "COORDINADOR")
    prof_id = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = TareaService(session, tid)
            tarea = await svc.create(TareaCreate(asignado_a=prof_id, descripcion="Test"),
                                     user_id=coord_id, roles=["COORDINADOR"])
            await session.commit()
            tarea_id = tarea.id

        async with db_setup() as session:
            svc = TareaService(session, tid)
            await svc.delete(tarea_id, user_id=coord_id, roles=["COORDINADOR"])
            await session.commit()

        async with db_setup() as session:
            svc = TareaService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.get(tarea_id, user_id=coord_id, roles=["COORDINADOR"])
            assert exc.value.status_code == 404
    finally:
        reset_tenant_context(token)


async def test_eliminar_tarea_profesor_raise_403(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    prof_id = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = TareaService(session, tid)
            tarea = await svc.create(TareaCreate(asignado_a=prof_id, descripcion="Test"),
                                     user_id=prof_id, roles=["PROFESOR"])
            await session.commit()
            tarea_id = tarea.id

        async with db_setup() as session:
            svc = TareaService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.delete(tarea_id, user_id=prof_id, roles=["PROFESOR"])
            assert exc.value.status_code == 403
    finally:
        reset_tenant_context(token)


# ═══════════════════════════════════════════════════════════════════════
# 5. Comentarios
# ═══════════════════════════════════════════════════════════════════════

async def test_agregar_comentario_coordinador(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    coord_id = await _setup_user(db_setup, tid, role_ids, "COORDINADOR")
    prof_id = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = TareaService(session, tid)
            tarea = await svc.create(TareaCreate(asignado_a=prof_id, descripcion="Test"),
                                     user_id=coord_id, roles=["COORDINADOR"])
            await session.commit()
            tarea_id = tarea.id

        async with db_setup() as session:
            svc = TareaService(session, tid)
            comentario = await svc.agregar_comentario(
                tarea_id, ComentarioCreate(texto="Revisado, corregir fechas"),
                user_id=coord_id, roles=["COORDINADOR"],
            )
            await session.commit()
            assert comentario.id is not None
            assert comentario.texto == "Revisado, corregir fechas"
            assert comentario.autor_id == coord_id
    finally:
        reset_tenant_context(token)


async def test_agregar_comentario_profesor_propio(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    prof_id = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = TareaService(session, tid)
            tarea = await svc.create(TareaCreate(asignado_a=prof_id, descripcion="Test"),
                                     user_id=prof_id, roles=["PROFESOR"])
            await session.commit()
            tarea_id = tarea.id

        async with db_setup() as session:
            svc = TareaService(session, tid)
            comentario = await svc.agregar_comentario(
                tarea_id, ComentarioCreate(texto="Listo para revision"),
                user_id=prof_id, roles=["PROFESOR"],
            )
            await session.commit()
            assert comentario.texto == "Listo para revision"
    finally:
        reset_tenant_context(token)


async def test_agregar_comentario_profesor_ajeno_raise_404(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    prof_a = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    prof_b = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = TareaService(session, tid)
            tarea = await svc.create(TareaCreate(asignado_a=prof_a, descripcion="Test"),
                                     user_id=prof_a, roles=["PROFESOR"])
            await session.commit()
            tarea_id = tarea.id

        async with db_setup() as session:
            svc = TareaService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.agregar_comentario(
                    tarea_id, ComentarioCreate(texto="Hola"),
                    user_id=prof_b, roles=["PROFESOR"],
                )
            assert exc.value.status_code == 404
    finally:
        reset_tenant_context(token)


async def test_agregar_comentario_tarea_inexistente_raise_404(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    coord_id = await _setup_user(db_setup, tid, role_ids, "COORDINADOR")
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = TareaService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.agregar_comentario(
                    uuid4(), ComentarioCreate(texto="Hola"),
                    user_id=coord_id, roles=["COORDINADOR"],
                )
            assert exc.value.status_code == 404
    finally:
        reset_tenant_context(token)


async def test_agregar_comentario_texto_vacio_raise_422(db_setup) -> None:
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        ComentarioCreate(texto="")


async def test_listar_comentarios_coordinador(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    coord_id = await _setup_user(db_setup, tid, role_ids, "COORDINADOR")
    prof_id = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = TareaService(session, tid)
            tarea = await svc.create(TareaCreate(asignado_a=prof_id, descripcion="Test"),
                                     user_id=coord_id, roles=["COORDINADOR"])
            await session.commit()
            tarea_id = tarea.id

        async with db_setup() as session:
            svc = TareaService(session, tid)
            await svc.agregar_comentario(
                tarea_id, ComentarioCreate(texto="Primero"),
                user_id=coord_id, roles=["COORDINADOR"],
            )
            await svc.agregar_comentario(
                tarea_id, ComentarioCreate(texto="Segundo"),
                user_id=prof_id, roles=["PROFESOR"],
            )
            await session.commit()

        async with db_setup() as session:
            svc = TareaService(session, tid)
            items, total = await svc.listar_comentarios(tarea_id, user_id=coord_id, roles=["COORDINADOR"])
            assert total == 2
            assert len(items) == 2
            assert items[0].texto == "Primero"
            assert items[1].texto == "Segundo"
    finally:
        reset_tenant_context(token)


async def test_listar_comentarios_profesor_propio(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    prof_id = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = TareaService(session, tid)
            tarea = await svc.create(TareaCreate(asignado_a=prof_id, descripcion="Test"),
                                     user_id=prof_id, roles=["PROFESOR"])
            await session.commit()
            tarea_id = tarea.id

        async with db_setup() as session:
            svc = TareaService(session, tid)
            await svc.agregar_comentario(tarea_id, ComentarioCreate(texto="Nota"),
                                         user_id=prof_id, roles=["PROFESOR"])
            await session.commit()

        async with db_setup() as session:
            svc = TareaService(session, tid)
            items, total = await svc.listar_comentarios(tarea_id, user_id=prof_id, roles=["PROFESOR"])
            assert total == 1
    finally:
        reset_tenant_context(token)


async def test_listar_comentarios_profesor_ajeno_raise_404(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    prof_a = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    prof_b = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = TareaService(session, tid)
            tarea = await svc.create(TareaCreate(asignado_a=prof_a, descripcion="Test"),
                                     user_id=prof_a, roles=["PROFESOR"])
            await session.commit()
            tarea_id = tarea.id

        async with db_setup() as session:
            svc = TareaService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.listar_comentarios(tarea_id, user_id=prof_b, roles=["PROFESOR"])
            assert exc.value.status_code == 404
    finally:
        reset_tenant_context(token)


# ═══════════════════════════════════════════════════════════════════════
# 6. Visibilidad — Mis tareas
# ═══════════════════════════════════════════════════════════════════════

async def test_mis_tareas_profesor(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    prof_id = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    coord_id = await _setup_user(db_setup, tid, role_ids, "COORDINADOR")
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = TareaService(session, tid)
            await svc.create(TareaCreate(asignado_a=prof_id, descripcion="Tarea del profe"),
                             user_id=coord_id, roles=["COORDINADOR"])
            await svc.create(TareaCreate(asignado_a=coord_id, descripcion="Tarea del coord"),
                             user_id=coord_id, roles=["COORDINADOR"])
            await session.commit()

        async with db_setup() as session:
            svc = TareaService(session, tid)
            items, total = await svc.list_mis_tareas(prof_id, page=1, per_page=20)
            assert total == 1
            assert items[0].asignado_a == prof_id
    finally:
        reset_tenant_context(token)


async def test_mis_tareas_filtro_estado(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    prof_id = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = TareaService(session, tid)
            t1 = await svc.create(TareaCreate(asignado_a=prof_id, descripcion="Pendiente"),
                                  user_id=prof_id, roles=["PROFESOR"])
            await session.commit()
            t1_id = t1.id

        async with db_setup() as session:
            svc = TareaService(session, tid)
            t2 = await svc.create(TareaCreate(asignado_a=prof_id, descripcion="En progreso"),
                                  user_id=prof_id, roles=["PROFESOR"])
            await session.commit()
            t2_id = t2.id

        async with db_setup() as session:
            svc = TareaService(session, tid)
            await svc.update(t2_id, TareaUpdate(estado="En progreso"),
                             user_id=prof_id, roles=["PROFESOR"])
            await session.commit()

        async with db_setup() as session:
            svc = TareaService(session, tid)
            items, total = await svc.list_mis_tareas(prof_id, estado="Pendiente")
            assert total == 1
            assert items[0].id == t1_id
    finally:
        reset_tenant_context(token)


async def test_mis_tareas_filtro_materia(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    prof_id = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    materia_id = uuid4()
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = TareaService(session, tid)
            await svc.create(TareaCreate(asignado_a=prof_id, descripcion="Sin materia"),
                             user_id=prof_id, roles=["PROFESOR"])
            await svc.create(TareaCreate(asignado_a=prof_id, descripcion="Con materia", materia_id=materia_id),
                             user_id=prof_id, roles=["PROFESOR"])
            await session.commit()

        async with db_setup() as session:
            svc = TareaService(session, tid)
            items, total = await svc.list_mis_tareas(prof_id, materia_id=materia_id)
            assert total == 1
            assert items[0].materia_id == materia_id
    finally:
        reset_tenant_context(token)


# ═══════════════════════════════════════════════════════════════════════
# 7. Visibilidad — Listar todas (admin)
# ═══════════════════════════════════════════════════════════════════════

async def test_listar_todas_coordinador(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    coord_id = await _setup_user(db_setup, tid, role_ids, "COORDINADOR")
    prof_a = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    prof_b = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = TareaService(session, tid)
            await svc.create(TareaCreate(asignado_a=prof_a, descripcion="A"),
                             user_id=coord_id, roles=["COORDINADOR"])
            await svc.create(TareaCreate(asignado_a=prof_b, descripcion="B"),
                             user_id=coord_id, roles=["COORDINADOR"])
            await session.commit()

        async with db_setup() as session:
            svc = TareaService(session, tid)
            items, total = await svc.list_all(user_id=coord_id, roles=["COORDINADOR"], page=1, per_page=20)
            assert total == 2
    finally:
        reset_tenant_context(token)


async def test_listar_todas_filtro_asignado_a(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    coord_id = await _setup_user(db_setup, tid, role_ids, "COORDINADOR")
    prof_a = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    prof_b = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = TareaService(session, tid)
            await svc.create(TareaCreate(asignado_a=prof_a, descripcion="A"),
                             user_id=coord_id, roles=["COORDINADOR"])
            await svc.create(TareaCreate(asignado_a=prof_b, descripcion="B"),
                             user_id=coord_id, roles=["COORDINADOR"])
            await session.commit()

        async with db_setup() as session:
            svc = TareaService(session, tid)
            items, total = await svc.list_all(user_id=coord_id, roles=["COORDINADOR"], asignado_a=prof_a)
            assert total == 1
            assert items[0].asignado_a == prof_a
    finally:
        reset_tenant_context(token)


async def test_listar_todas_filtro_estado(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    coord_id = await _setup_user(db_setup, tid, role_ids, "COORDINADOR")
    prof_id = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = TareaService(session, tid)
            await svc.create(TareaCreate(asignado_a=prof_id, descripcion="Pendiente"),
                             user_id=coord_id, roles=["COORDINADOR"])
            await session.commit()

        async with db_setup() as session:
            svc = TareaService(session, tid)
            t2 = await svc.create(TareaCreate(asignado_a=prof_id, descripcion="En progreso"),
                                  user_id=coord_id, roles=["COORDINADOR"])
            await session.commit()
            t2_id = t2.id

        async with db_setup() as session:
            svc = TareaService(session, tid)
            await svc.update(t2_id, TareaUpdate(estado="En progreso"),
                             user_id=coord_id, roles=["COORDINADOR"])
            await session.commit()

        async with db_setup() as session:
            svc = TareaService(session, tid)
            items, total = await svc.list_all(user_id=coord_id, roles=["COORDINADOR"], estado="En progreso")
            assert total == 1
            assert items[0].id == t2_id
    finally:
        reset_tenant_context(token)


async def test_listar_todas_busqueda_texto(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    coord_id = await _setup_user(db_setup, tid, role_ids, "COORDINADOR")
    prof_id = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = TareaService(session, tid)
            await svc.create(TareaCreate(asignado_a=prof_id, descripcion="Preparar examen final"),
                             user_id=coord_id, roles=["COORDINADOR"])
            await svc.create(TareaCreate(asignado_a=prof_id, descripcion="Revisar guias"),
                             user_id=coord_id, roles=["COORDINADOR"])
            await session.commit()

        async with db_setup() as session:
            svc = TareaService(session, tid)
            items, total = await svc.list_all(user_id=coord_id, roles=["COORDINADOR"], q="examen")
            assert total == 1
            assert "examen" in items[0].descripcion.lower()
    finally:
        reset_tenant_context(token)


async def test_listar_todas_profesor_raise_403(db_setup) -> None:
    tid, role_ids = await _setup_tenant(db_setup)
    prof_id = await _setup_user(db_setup, tid, role_ids, "PROFESOR")
    token = set_tenant_context(TenantContext(tenant_id=tid))
    try:
        async with db_setup() as session:
            svc = TareaService(session, tid)
            with pytest.raises(HTTPException) as exc:
                await svc.list_all(user_id=prof_id, roles=["PROFESOR"])
            assert exc.value.status_code == 403
    finally:
        reset_tenant_context(token)
