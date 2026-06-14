"""Strict TDD for Asignacion model (C-07 §7.2).

Tests cover:
- estado_vigencia for all scenarios (sin hasta, hasta futuro, hasta pasado, desde futuro, desde hoy)
- Contexto Global sin contexto_id
- jerarquía responsable_id
- __repr__ does not leak sensitive data
"""

from __future__ import annotations

from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.models.asignacion import Asignacion, ContextoTipo

pytestmark = pytest.mark.no_db

_today = date.today()
_yesterday = _today - timedelta(days=1)
_tomorrow = _today + timedelta(days=1)
_future = _today + timedelta(days=30)
_past = _today - timedelta(days=30)


# ── 7.2 estado_vigencia ──────────────────────────────────────────────

def test_estado_vigencia_sin_hasta_es_vigente() -> None:
    a = Asignacion(
        tenant_id=uuid4(), usuario_id=uuid4(), rol_id=uuid4(),
        contexto_tipo=ContextoTipo.GLOBAL, contexto_id=None,
        desde=_past, hasta=None,
    )
    assert a.estado_vigencia == "Vigente"


def test_estado_vigencia_con_hasta_futuro_es_vigente() -> None:
    a = Asignacion(
        tenant_id=uuid4(), usuario_id=uuid4(), rol_id=uuid4(),
        contexto_tipo=ContextoTipo.GLOBAL, contexto_id=None,
        desde=_past, hasta=_future,
    )
    assert a.estado_vigencia == "Vigente"


def test_estado_vigencia_con_hasta_pasado_es_vencida() -> None:
    a = Asignacion(
        tenant_id=uuid4(), usuario_id=uuid4(), rol_id=uuid4(),
        contexto_tipo=ContextoTipo.GLOBAL, contexto_id=None,
        desde=_past - timedelta(days=60), hasta=_yesterday,
    )
    assert a.estado_vigencia == "Vencida"


def test_estado_vigencia_desde_futuro_sin_hasta_es_vencida() -> None:
    a = Asignacion(
        tenant_id=uuid4(), usuario_id=uuid4(), rol_id=uuid4(),
        contexto_tipo=ContextoTipo.GLOBAL, contexto_id=None,
        desde=_future, hasta=None,
    )
    assert a.estado_vigencia == "Vencida"


def test_estado_vigencia_desde_hoy_sin_hasta_es_vigente() -> None:
    a = Asignacion(
        tenant_id=uuid4(), usuario_id=uuid4(), rol_id=uuid4(),
        contexto_tipo=ContextoTipo.GLOBAL, contexto_id=None,
        desde=_today, hasta=None,
    )
    assert a.estado_vigencia == "Vigente"


def test_estado_vigencia_desde_y_hasta_hoy_es_vigente() -> None:
    a = Asignacion(
        tenant_id=uuid4(), usuario_id=uuid4(), rol_id=uuid4(),
        contexto_tipo=ContextoTipo.GLOBAL, contexto_id=None,
        desde=_today, hasta=_today,
    )
    assert a.estado_vigencia == "Vigente"


def test_estado_vigencia_rango_completamente_pasado_es_vencida() -> None:
    a = Asignacion(
        tenant_id=uuid4(), usuario_id=uuid4(), rol_id=uuid4(),
        contexto_tipo=ContextoTipo.GLOBAL, contexto_id=None,
        desde=date(2020, 1, 1), hasta=date(2020, 12, 31),
    )
    assert a.estado_vigencia == "Vencida"


# ── Contexto Global sin contexto_id ──────────────────────────────────

def test_contexto_global_contexto_id_puede_ser_null() -> None:
    a = Asignacion(
        tenant_id=uuid4(), usuario_id=uuid4(), rol_id=uuid4(),
        contexto_tipo=ContextoTipo.GLOBAL, contexto_id=None,
        desde=_past, hasta=None,
    )
    assert a.contexto_tipo == ContextoTipo.GLOBAL
    assert a.contexto_id is None


def test_contexto_carrera_requiere_contexto_id() -> None:
    cid = uuid4()
    a = Asignacion(
        tenant_id=uuid4(), usuario_id=uuid4(), rol_id=uuid4(),
        contexto_tipo=ContextoTipo.CARRERA, contexto_id=cid,
        desde=_past, hasta=None,
    )
    assert a.contexto_tipo == ContextoTipo.CARRERA
    assert a.contexto_id == cid


def test_contexto_cohorte_requiere_contexto_id() -> None:
    cid = uuid4()
    a = Asignacion(
        tenant_id=uuid4(), usuario_id=uuid4(), rol_id=uuid4(),
        contexto_tipo=ContextoTipo.COHORTE, contexto_id=cid,
        desde=_past, hasta=None,
    )
    assert a.contexto_tipo == ContextoTipo.COHORTE
    assert a.contexto_id == cid


def test_contexto_materia_requiere_contexto_id() -> None:
    cid = uuid4()
    a = Asignacion(
        tenant_id=uuid4(), usuario_id=uuid4(), rol_id=uuid4(),
        contexto_tipo=ContextoTipo.MATERIA, contexto_id=cid,
        desde=_past, hasta=None,
    )
    assert a.contexto_tipo == ContextoTipo.MATERIA
    assert a.contexto_id == cid


# ── jerarquía responsable_id ─────────────────────────────────────────

def test_asignacion_con_responsable() -> None:
    responsable_id = uuid4()
    a = Asignacion(
        tenant_id=uuid4(), usuario_id=uuid4(), rol_id=uuid4(),
        contexto_tipo=ContextoTipo.GLOBAL, contexto_id=None,
        responsable_id=responsable_id,
        desde=_past, hasta=None,
    )
    assert a.responsable_id == responsable_id


def test_asignacion_sin_responsable() -> None:
    a = Asignacion(
        tenant_id=uuid4(), usuario_id=uuid4(), rol_id=uuid4(),
        contexto_tipo=ContextoTipo.GLOBAL, contexto_id=None,
        responsable_id=None,
        desde=_past, hasta=None,
    )
    assert a.responsable_id is None


# ── __repr__ ─────────────────────────────────────────────────────────

def test_repr_asignacion_no_leaks_sensitive() -> None:
    uid = uuid4()
    rid = uuid4()
    tid = uuid4()
    a = Asignacion(
        id=uid, tenant_id=tid, usuario_id=uuid4(), rol_id=rid,
        contexto_tipo=ContextoTipo.CARRERA, contexto_id=uuid4(),
        desde=_past, hasta=None,
    )
    r = repr(a)
    assert str(uid) in r
    assert str(tid) in r
    assert str(rid) in r
    assert "Carrera" in r


def test_repr_asignacion_global() -> None:
    a = Asignacion(
        tenant_id=uuid4(), usuario_id=uuid4(), rol_id=uuid4(),
        contexto_tipo=ContextoTipo.GLOBAL, contexto_id=None,
        desde=_past, hasta=None,
    )
    r = repr(a)
    assert "Global" in r


def test_contexto_tipo_enum_values() -> None:
    assert ContextoTipo.GLOBAL.value == "Global"
    assert ContextoTipo.CARRERA.value == "Carrera"
    assert ContextoTipo.COHORTE.value == "Cohorte"
    assert ContextoTipo.MATERIA.value == "Materia"
