"""seed_domain.py — Datos académicos de desarrollo para activia-trace.

Crea sobre el tenant DEV:
  - 1 Carrera: Tecnicatura Universitaria en Programación (TUP)
  - 1 Cohorte: 2026
  - 3 Materias: AED, POO, BD
  - 5 alumnos con padrón, calificaciones y umbrales
  - Asignaciones contextuales: PROFESOR -> AED+POO, TUTOR -> AED
  - SlotEncuentro AED (Lunes 18-20hs, 4 semanas) + 4 instancias
  - 1 InstanciaEncuentro única (POO)
  - 1 Guardia (TUTOR en AED)
  - 2 Comunicaciones Pendiente en un lote para probar el flujo de aprobación

Prerrequisito: ejecutar seed_dev.py primero (necesita tenant DEV y usuarios base).

Uso:
    python backend/scripts/seed_domain.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import date, datetime, time, timezone
from pathlib import Path
from uuid import UUID, uuid4

_repo_root = Path(__file__).resolve().parents[2]
_backend_root = _repo_root / "backend"
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

import json

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.security.crypto import encrypt
from app.core.security.hashing import hash_email_for_search
from app.core.security.passwords import hash_password

_DEV_ENV_DEFAULTS: dict[str, str] = {
    "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:5432/activia_trace_test",
    "SECRET_KEY": "dev-secret-key-minimum-32-characters-long",
    "ENCRYPTION_KEY": "01234567890123456789012345678901",
}
for _k, _v in _DEV_ENV_DEFAULTS.items():
    os.environ.setdefault(_k, _v)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

_T = UUID("11111111-2222-3333-4444-555555555555")  # DEV tenant
_PLAINTEXT_PASSWORD = "Admin123!"

_ROL_IDS = {
    "ALUMNO":      UUID("00000000-0000-0000-0000-a00000000001"),
    "TUTOR":       UUID("00000000-0000-0000-0000-a00000000002"),
    "PROFESOR":    UUID("00000000-0000-0000-0000-a00000000003"),
    "COORDINADOR": UUID("00000000-0000-0000-0000-a00000000004"),
}

# Estructura académica
_CARRERA  = UUID("22222222-0001-0000-0000-000000000000")
_COHORTE  = UUID("22222222-0002-0000-0000-000000000000")
_MAT_AED  = UUID("22222222-0003-0000-0000-000000000000")
_MAT_POO  = UUID("22222222-0004-0000-0000-000000000000")
_MAT_BD   = UUID("22222222-0005-0000-0000-000000000000")

# ProgramaMateria
_PROG_AED = UUID("22222222-0011-0000-0000-000000000000")
_PROG_POO = UUID("22222222-0012-0000-0000-000000000000")
_PROG_BD  = UUID("22222222-0013-0000-0000-000000000000")

# Alumnos (auth_user.id == usuario.id)
_A1 = UUID("33333333-0001-0000-0000-000000000000")  # Juan García
_A2 = UUID("33333333-0002-0000-0000-000000000000")  # María López
_A3 = UUID("33333333-0003-0000-0000-000000000000")  # Carlos Martínez (atrasado)
_A4 = UUID("33333333-0004-0000-0000-000000000000")  # Ana Rodríguez
_A5 = UUID("33333333-0005-0000-0000-000000000000")  # Pedro Sánchez (sin nota)

_ALUMNOS = [
    (_A1, "alumno1@dev.com", "Juan",    "García"),
    (_A2, "alumno2@dev.com", "María",   "López"),
    (_A3, "alumno3@dev.com", "Carlos",  "Martínez"),
    (_A4, "alumno4@dev.com", "Ana",     "Rodríguez"),
    (_A5, "alumno5@dev.com", "Pedro",   "Sánchez"),
]

# Padrón
_VP_AED = UUID("22222222-0021-0000-0000-000000000000")
_VP_POO = UUID("22222222-0022-0000-0000-000000000000")

_EP_AED = [UUID(f"22222222-0031-0000-0000-{i:012d}") for i in range(1, 6)]
_EP_POO = [UUID(f"22222222-0032-0000-0000-{i:012d}") for i in range(1, 5)]

# Umbrales
_UM_AED = UUID("22222222-0041-0000-0000-000000000000")
_UM_POO = UUID("22222222-0042-0000-0000-000000000000")

# Calificaciones
_CAL_AED = [UUID(f"44444444-0001-0000-0000-{i:012d}") for i in range(1, 6)]
_CAL_POO = [UUID(f"44444444-0002-0000-0000-{i:012d}") for i in range(1, 5)]

# Encuentros
_SLOT     = UUID("55555555-0001-0000-0000-000000000000")
_INS_SLOT = [UUID(f"55555555-0002-0000-0000-{i:012d}") for i in range(1, 5)]
_INS_UNICA = UUID("55555555-0003-0000-0000-000000000001")
_GUARDIA   = UUID("55555555-0004-0000-0000-000000000001")
_GUARDIAS_PROFESOR = [
    UUID("55555555-0005-0000-0000-000000000001"),
    UUID("55555555-0005-0000-0000-000000000002"),
]

# Comunicaciones
_LOTE_ID = UUID("22222222-0051-0000-0000-000000000000")
_COM_IDS  = [UUID(f"66666666-0001-0000-0000-{i:012d}") for i in range(1, 4)]

# Inbox interna PROFESOR
_HILO_COORDINACION = UUID("77777777-0001-0000-0000-000000000001")
_HILO_TUTORIA = UUID("77777777-0001-0000-0000-000000000002")
_MSG_INTERNO_IDS = [UUID(f"77777777-0002-0000-0000-{i:012d}") for i in range(1, 5)]

# Fechas fijas (seed idempotente)
_HOY         = date(2026, 6, 19)
_SLOT_FECHAS = [date(2026, 7, 7), date(2026, 7, 14), date(2026, 7, 21), date(2026, 7, 28)]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _enc(plaintext: str, aad: str) -> str:
    return encrypt(plaintext, tenant_id=_T, aad_suffix=aad)


def _ehash(email: str) -> str:
    return hash_email_for_search(email.lower(), _T)


def _build_professor_guardias(profesor_id: UUID) -> list[dict[str, object]]:
    return [
        {
            "id": _GUARDIAS_PROFESOR[0],
            "tutor_id": profesor_id,
            "materia_id": _MAT_AED,
            "cohorte_id": _COHORTE,
            "fecha": date(2026, 7, 10),
            "hora_inicio": time(18, 30),
            "hora_fin": time(20, 0),
            "titulo": "Consultorio AED - recuperacion TP2",
            "observaciones": "Repaso de estructuras enlazadas y criterio de evaluacion.",
        },
        {
            "id": _GUARDIAS_PROFESOR[1],
            "tutor_id": profesor_id,
            "materia_id": _MAT_POO,
            "cohorte_id": _COHORTE,
            "fecha": date(2026, 7, 16),
            "hora_inicio": time(19, 0),
            "hora_fin": time(20, 30),
            "titulo": "Consultorio POO - UML y entregables",
            "observaciones": "Guardia previa al coloquio con foco en herencia y modelado.",
        },
    ]


def _build_professor_inbox_messages(
    profesor_id: UUID,
    coordinador_id: UUID,
    tutor_id: UUID,
) -> list[dict[str, object]]:
    return [
        {
            "id": _MSG_INTERNO_IDS[0],
            "hilo_id": _HILO_COORDINACION,
            "padre_id": None,
            "asunto": "Seguimiento de alumnos AED",
            "cuerpo": "Necesito que revises a Carlos Martinez y Pedro Sanchez antes del cierre semanal.",
            "remitente_id": coordinador_id,
            "destinatario_id": profesor_id,
            "created_at": datetime(2026, 6, 17, 14, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 6, 17, 14, 0, tzinfo=timezone.utc),
            "leido_at": datetime(2026, 6, 17, 14, 5, tzinfo=timezone.utc),
        },
        {
            "id": _MSG_INTERNO_IDS[1],
            "hilo_id": _HILO_COORDINACION,
            "padre_id": _MSG_INTERNO_IDS[0],
            "asunto": "Re: Seguimiento de alumnos AED",
            "cuerpo": "Ya revise ambos casos. Carlos necesita recuperatorio y Pedro sigue sin nota cargada.",
            "remitente_id": profesor_id,
            "destinatario_id": coordinador_id,
            "created_at": datetime(2026, 6, 17, 15, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 6, 17, 15, 0, tzinfo=timezone.utc),
            "leido_at": datetime(2026, 6, 17, 15, 10, tzinfo=timezone.utc),
        },
        {
            "id": _MSG_INTERNO_IDS[2],
            "hilo_id": _HILO_COORDINACION,
            "padre_id": _MSG_INTERNO_IDS[1],
            "asunto": "Re: Seguimiento de alumnos AED",
            "cuerpo": "Perfecto. Dejemos trazado ese seguimiento para la demo con coordinacion.",
            "remitente_id": coordinador_id,
            "destinatario_id": profesor_id,
            "created_at": datetime(2026, 6, 17, 16, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 6, 17, 16, 0, tzinfo=timezone.utc),
            "leido_at": None,
        },
        {
            "id": _MSG_INTERNO_IDS[3],
            "hilo_id": _HILO_TUTORIA,
            "padre_id": None,
            "asunto": "Material de apoyo POO",
            "cuerpo": "Te comparto la guia de polimorfismo para que la uses en la proxima guardia.",
            "remitente_id": tutor_id,
            "destinatario_id": profesor_id,
            "created_at": datetime(2026, 6, 18, 11, 30, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 6, 18, 11, 30, tzinfo=timezone.utc),
            "leido_at": datetime(2026, 6, 18, 12, 0, tzinfo=timezone.utc),
        },
    ]


async def _get_user_id(conn: sa.ext.asyncio.AsyncConnection, email: str) -> UUID | None:
    row = (await conn.execute(
        sa.text("SELECT id FROM auth_user WHERE tenant_id=:t AND email_hash=:h AND deleted_at IS NULL"),
        {"t": str(_T), "h": _ehash(email)},
    )).fetchone()
    return UUID(str(row[0])) if row else None


# ---------------------------------------------------------------------------
# Pasos de seed
# ---------------------------------------------------------------------------

async def _ensure_alumnos(conn: sa.ext.asyncio.AsyncConnection) -> None:
    print("\n=== Alumnos ===")
    for uid, email, nombre, apellidos in _ALUMNOS:
        email_lower = email.lower()
        email_hash  = _ehash(email_lower)
        email_enc   = _enc(email_lower, "email")
        pw_hash     = hash_password(_PLAINTEXT_PASSWORD)

        existing = (await conn.execute(
            sa.text("SELECT id FROM auth_user WHERE id=:id"),
            {"id": str(uid)},
        )).fetchone()

        if existing:
            print(f"  [skip]  {email}")
            continue

        dni_enc  = _enc("00000000",             "dni")
        cuil_enc = _enc("20000000009",           "cuil")
        cbu_enc  = _enc("0000000000000000000000","cbu")

        await conn.execute(sa.text("""
            INSERT INTO auth_user
                (id, tenant_id, email_enc, email_hash, password_hash,
                 totp_secret_enc, totp_enabled, is_active,
                 failed_login_count, last_login_at, created_at, updated_at, deleted_at)
            VALUES
                (:id, :t, :email_enc, :email_hash, :pw_hash,
                 NULL, false, true, 0, NULL, now(), now(), NULL)
            ON CONFLICT (id) DO NOTHING
        """), {"id": str(uid), "t": str(_T), "email_enc": email_enc,
               "email_hash": email_hash, "pw_hash": pw_hash})

        await conn.execute(sa.text("""
            INSERT INTO usuario
                (id, tenant_id, email_hash, email_enc,
                 dni_enc, cuil_enc, cbu_enc, alias_cbu_enc,
                 nombre, apellidos,
                 banco, regional, legajo, legajo_profesional,
                 fecha_nacimiento, genero, observaciones,
                 created_at, updated_at, deleted_at)
            VALUES
                (:id, :t, :email_hash, :email_enc,
                 :dni_enc, :cuil_enc, :cbu_enc, NULL,
                 :nombre, :apellidos,
                 NULL, NULL, NULL, NULL,
                 NULL, NULL, NULL,
                 now(), now(), NULL)
            ON CONFLICT (tenant_id, email_hash) DO NOTHING
        """), {"id": str(uid), "t": str(_T), "email_hash": email_hash,
               "email_enc": email_enc, "dni_enc": dni_enc,
               "cuil_enc": cuil_enc, "cbu_enc": cbu_enc,
               "nombre": nombre, "apellidos": apellidos})

        rol_id = _ROL_IDS["ALUMNO"]
        asig_existing = (await conn.execute(
            sa.text("SELECT id FROM asignacion WHERE tenant_id=:t AND usuario_id=:uid AND rol_id=:rid AND deleted_at IS NULL"),
            {"t": str(_T), "uid": str(uid), "rid": str(rol_id)},
        )).fetchone()
        if not asig_existing:
            await conn.execute(sa.text("""
                INSERT INTO asignacion
                    (id, tenant_id, usuario_id, rol_id,
                     contexto_tipo, contexto_id, responsable_id,
                     desde, hasta, created_at, updated_at, deleted_at)
                VALUES
                    (:id, :t, :uid, :rid,
                     'Global', NULL, NULL,
                     :desde, NULL, now(), now(), NULL)
            """), {"id": str(uuid4()), "t": str(_T), "uid": str(uid),
                   "rid": str(rol_id), "desde": _HOY})

        print(f"  [ok]    {email}  ({nombre} {apellidos})")


async def _ensure_estructura(conn: sa.ext.asyncio.AsyncConnection) -> None:
    print("\n=== Estructura académica ===")

    await conn.execute(sa.text("""
        INSERT INTO carrera (id, tenant_id, codigo, nombre, estado, created_at, updated_at, deleted_at)
        VALUES (:id, :t, 'TUP', 'Tecnicatura Universitaria en Programación', 'Activa', now(), now(), NULL)
        ON CONFLICT (id) DO NOTHING
    """), {"id": str(_CARRERA), "t": str(_T)})
    print("  [ok]  Carrera TUP")

    await conn.execute(sa.text("""
        INSERT INTO cohorte (id, tenant_id, carrera_id, nombre, anio, vig_desde, vig_hasta, estado, created_at, updated_at, deleted_at)
        VALUES (:id, :t, :cid, '2026', 2026, '2026-03-01', NULL, 'Activa', now(), now(), NULL)
        ON CONFLICT (id) DO NOTHING
    """), {"id": str(_COHORTE), "t": str(_T), "cid": str(_CARRERA)})
    print("  [ok]  Cohorte 2026")

    for mat_id, codigo, nombre in [
        (_MAT_AED, "AED", "Algoritmos y Estructuras de Datos"),
        (_MAT_POO, "POO", "Programación Orientada a Objetos"),
        (_MAT_BD,  "BD",  "Base de Datos"),
    ]:
        await conn.execute(sa.text("""
            INSERT INTO materia (id, tenant_id, codigo, nombre, plus_grupo, estado, created_at, updated_at, deleted_at)
            VALUES (:id, :t, :codigo, :nombre, NULL, 'Activa', now(), now(), NULL)
            ON CONFLICT (id) DO NOTHING
        """), {"id": str(mat_id), "t": str(_T), "codigo": codigo, "nombre": nombre})
        print(f"  [ok]  Materia {codigo}")

    for prog_id, mat_id, titulo in [
        (_PROG_AED, _MAT_AED, "Programa AED 2026"),
        (_PROG_POO, _MAT_POO, "Programa POO 2026"),
        (_PROG_BD,  _MAT_BD,  "Programa BD 2026"),
    ]:
        await conn.execute(sa.text("""
            INSERT INTO programa_materia
                (id, tenant_id, materia_id, carrera_id, cohorte_id, titulo, referencia_archivo, created_at, updated_at, deleted_at)
            VALUES (:id, :t, :mid, :cid, :cohid, :titulo, NULL, now(), now(), NULL)
            ON CONFLICT (id) DO NOTHING
        """), {"id": str(prog_id), "t": str(_T), "mid": str(mat_id),
               "cid": str(_CARRERA), "cohid": str(_COHORTE), "titulo": titulo})
    print("  [ok]  ProgramaMateria (AED, POO, BD)")


async def _ensure_asignaciones_contextuales(
    conn: sa.ext.asyncio.AsyncConnection,
    profesor_id: UUID,
    tutor_id: UUID,
    coordinador_id: UUID,
) -> None:
    print("\n=== Asignaciones contextuales ===")

    # PROFESOR -> AED (Materia scope)
    # PROFESOR -> POO (Materia scope)
    for mat_id, label in [(_MAT_AED, "AED"), (_MAT_POO, "POO")]:
        exists = (await conn.execute(
            sa.text("""SELECT id FROM asignacion
                       WHERE tenant_id=:t AND usuario_id=:uid AND rol_id=:rid
                         AND contexto_tipo='Materia' AND materia_id=:mid AND deleted_at IS NULL"""),
            {"t": str(_T), "uid": str(profesor_id), "rid": str(_ROL_IDS["PROFESOR"]), "mid": str(mat_id)},
        )).fetchone()
        if not exists:
            await conn.execute(sa.text("""
                INSERT INTO asignacion
                    (id, tenant_id, usuario_id, rol_id,
                     contexto_tipo, contexto_id, materia_id, cohorte_id,
                     responsable_id, desde, hasta, created_at, updated_at, deleted_at)
                VALUES
                    (:id, :t, :uid, :rid,
                     'Materia', :mid, :mid, :cohid,
                     :responsable_id, :desde, :hasta, now(), now(), NULL)
            """), {"id": str(uuid4()), "t": str(_T), "uid": str(profesor_id),
                    "rid": str(_ROL_IDS["PROFESOR"]), "mid": str(mat_id),
                    "cohid": str(_COHORTE), "responsable_id": str(coordinador_id),
                    "desde": _HOY, "hasta": None})
            print(f"  [ok]  PROFESOR -> {label} (Materia)")
        else:
            print(f"  [skip] PROFESOR -> {label} ya existe")

    exists = (await conn.execute(
        sa.text("""SELECT id FROM asignacion
                   WHERE tenant_id=:t AND usuario_id=:uid AND rol_id=:rid
                     AND contexto_tipo='Materia' AND materia_id=:mid AND deleted_at IS NULL"""),
        {"t": str(_T), "uid": str(profesor_id), "rid": str(_ROL_IDS["PROFESOR"]), "mid": str(_MAT_BD)},
    )).fetchone()
    if not exists:
        await conn.execute(sa.text("""
            INSERT INTO asignacion
                (id, tenant_id, usuario_id, rol_id,
                 contexto_tipo, contexto_id, materia_id, cohorte_id,
                 responsable_id, desde, hasta, created_at, updated_at, deleted_at)
            VALUES
                (:id, :t, :uid, :rid,
                 'Materia', :mid, :mid, :cohid,
                 :responsable_id, :desde, :hasta, now(), now(), NULL)
        """), {"id": str(uuid4()), "t": str(_T), "uid": str(profesor_id),
               "rid": str(_ROL_IDS["PROFESOR"]), "mid": str(_MAT_BD),
               "cohid": str(_COHORTE), "responsable_id": str(coordinador_id),
               "desde": date(2026, 3, 1), "hasta": date(2026, 5, 31)})
        print("  [ok]  PROFESOR -> BD (Materia, historica)")
    else:
        print("  [skip] PROFESOR -> BD ya existe")

    # TUTOR -> AED (Materia scope)
    exists = (await conn.execute(
        sa.text("""SELECT id FROM asignacion
                   WHERE tenant_id=:t AND usuario_id=:uid AND rol_id=:rid
                     AND contexto_tipo='Materia' AND materia_id=:mid AND deleted_at IS NULL"""),
        {"t": str(_T), "uid": str(tutor_id), "rid": str(_ROL_IDS["TUTOR"]), "mid": str(_MAT_AED)},
    )).fetchone()
    if not exists:
        await conn.execute(sa.text("""
            INSERT INTO asignacion
                (id, tenant_id, usuario_id, rol_id,
                 contexto_tipo, contexto_id, materia_id, cohorte_id,
                 responsable_id, desde, hasta, created_at, updated_at, deleted_at)
            VALUES
                (:id, :t, :uid, :rid,
                 'Materia', :mid, :mid, :cohid,
                 NULL, :desde, NULL, now(), now(), NULL)
        """), {"id": str(uuid4()), "t": str(_T), "uid": str(tutor_id),
               "rid": str(_ROL_IDS["TUTOR"]), "mid": str(_MAT_AED),
               "cohid": str(_COHORTE), "desde": _HOY})
        print("  [ok]  TUTOR -> AED (Materia)")
    else:
        print("  [skip] TUTOR -> AED ya existe")


async def _ensure_padron(
    conn: sa.ext.asyncio.AsyncConnection,
    profesor_id: UUID,
) -> None:
    print("\n=== Padrón ===")
    actividades_aed = ["TP1", "TP2", "TP3", "Parcial", "Final"]
    actividades_poo = ["TP1", "TP2", "Final"]

    for vp_id, mat_id, actividades, label in [
        (_VP_AED, _MAT_AED, actividades_aed, "AED"),
        (_VP_POO, _MAT_POO, actividades_poo, "POO"),
    ]:
        await conn.execute(sa.text("""
            INSERT INTO version_padron
                (id, tenant_id, materia_id, cohorte_id, cargado_por, activa, actividades, created_at, updated_at, deleted_at)
            VALUES (:id, :t, :mid, :cohid, :uid, true, CAST(:acts AS jsonb), now(), now(), NULL)
            ON CONFLICT (id) DO NOTHING
        """), {"id": str(vp_id), "t": str(_T), "mid": str(mat_id),
               "cohid": str(_COHORTE), "uid": str(profesor_id),
               "acts": json.dumps(actividades)})
        print(f"  [ok]  VersionPadron {label}")

    # EntradaPadron para AED: los 5 alumnos
    for i, (ep_id, (uid, email, nombre, apellidos)) in enumerate(zip(_EP_AED, _ALUMNOS)):
        email_lower = email.lower()
        await conn.execute(sa.text("""
            INSERT INTO entrada_padron
                (id, tenant_id, version_id, usuario_id, nombre, apellidos,
                 email_hash, email_enc, comision, regional, created_at, updated_at, deleted_at)
            VALUES (:id, :t, :vid, :uid, :nombre, :apellidos,
                    :ehash, :eenc, 'A', NULL, now(), now(), NULL)
            ON CONFLICT (id) DO NOTHING
        """), {"id": str(ep_id), "t": str(_T), "vid": str(_VP_AED),
               "uid": str(uid), "nombre": nombre, "apellidos": apellidos,
               "ehash": _ehash(email_lower),
               "eenc": _enc(email_lower, "entrada_padron.email")})
    print("  [ok]  EntradaPadron AED (5 alumnos)")

    # EntradaPadron para POO: primeros 4 alumnos
    for ep_id, (uid, email, nombre, apellidos) in zip(_EP_POO, _ALUMNOS[:4]):
        email_lower = email.lower()
        await conn.execute(sa.text("""
            INSERT INTO entrada_padron
                (id, tenant_id, version_id, usuario_id, nombre, apellidos,
                 email_hash, email_enc, comision, regional, created_at, updated_at, deleted_at)
            VALUES (:id, :t, :vid, :uid, :nombre, :apellidos,
                    :ehash, :eenc, 'A', NULL, now(), now(), NULL)
            ON CONFLICT (id) DO NOTHING
        """), {"id": str(ep_id), "t": str(_T), "vid": str(_VP_POO),
               "uid": str(uid), "nombre": nombre, "apellidos": apellidos,
               "ehash": _ehash(email_lower),
               "eenc": _enc(email_lower, "entrada_padron.email")})
    print("  [ok]  EntradaPadron POO (4 alumnos)")


async def _ensure_umbrales(conn: sa.ext.asyncio.AsyncConnection) -> None:
    print("\n=== Umbrales ===")
    for um_id, mat_id, label in [(_UM_AED, _MAT_AED, "AED"), (_UM_POO, _MAT_POO, "POO")]:
        await conn.execute(sa.text("""
            INSERT INTO umbral_materia
                (id, tenant_id, materia_id, asignacion_id, umbral_pct, conjunto_aprobado, created_at, updated_at, deleted_at)
            VALUES (:id, :t, :mid, NULL, 60, NULL, now(), now(), NULL)
            ON CONFLICT (id) DO NOTHING
        """), {"id": str(um_id), "t": str(_T), "mid": str(mat_id)})
        print(f"  [ok]  UmbralMateria {label} = 60%  (nota >= 6 aprueba)")


async def _ensure_calificaciones(conn: sa.ext.asyncio.AsyncConnection) -> None:
    print("\n=== Calificaciones ===")
    # AED: notas 8, 7, 4, 9, null
    aed_notas: list[int | None] = [8, 7, 4, 9, None]
    for cal_id, (uid, _, nombre, apellidos), nota in zip(_CAL_AED, _ALUMNOS, aed_notas):
        nota_param = json.dumps(nota)  # None -> "null", 8 -> "8"
        await conn.execute(sa.text("""
            INSERT INTO calificacion
                (id, tenant_id, materia_id, usuario_id, asignacion_id,
                 version_padron_id, nota, origen, import_batch_id, created_by,
                 created_at, updated_at, deleted_at)
            VALUES (:id, :t, :mid, :uid, NULL,
                    :vpid, CAST(:nota AS jsonb), 'manual', NULL, NULL,
                    now(), now(), NULL)
            ON CONFLICT (id) DO NOTHING
        """), {"id": str(cal_id), "t": str(_T), "mid": str(_MAT_AED),
               "uid": str(uid), "vpid": str(_VP_AED), "nota": nota_param})
        estado = "OK" if nota is not None and nota >= 6 else ("FAIL" if nota is not None else "—")
        print(f"  [ok]  AED {nombre} {apellidos}: nota={nota}  {estado}")

    # POO: notas 7, 6, 3, 8 (alumnos 1-4)
    poo_notas = [7, 6, 3, 8]
    for cal_id, (uid, _, nombre, apellidos), nota in zip(_CAL_POO, _ALUMNOS[:4], poo_notas):
        await conn.execute(sa.text("""
            INSERT INTO calificacion
                (id, tenant_id, materia_id, usuario_id, asignacion_id,
                 version_padron_id, nota, origen, import_batch_id, created_by,
                 created_at, updated_at, deleted_at)
            VALUES (:id, :t, :mid, :uid, NULL,
                    :vpid, CAST(:nota AS jsonb), 'manual', NULL, NULL,
                    now(), now(), NULL)
            ON CONFLICT (id) DO NOTHING
        """), {"id": str(cal_id), "t": str(_T), "mid": str(_MAT_POO),
               "uid": str(uid), "vpid": str(_VP_POO), "nota": json.dumps(nota)})
        estado = "OK" if nota >= 6 else "FAIL"
        print(f"  [ok]  POO {nombre} {apellidos}: nota={nota}  {estado}")


async def _ensure_encuentros(
    conn: sa.ext.asyncio.AsyncConnection,
    tutor_id: UUID,
    profesor_id: UUID,
) -> None:
    print("\n=== Encuentros ===")

    # SlotEncuentro: AED — Lunes 18-20hs, 4 semanas desde 2026-07-07
    await conn.execute(sa.text("""
        INSERT INTO slot_encuentro
            (id, tenant_id, materia_id, cohorte_id, titulo,
             dia_semana, hora_inicio, hora_fin, fecha_inicio, cant_semanas,
             meet_url, video_url, created_at, updated_at, deleted_at)
        VALUES (:id, :t, :mid, :cohid, 'Teórica AED',
                0, '18:00', '20:00', :fi, 4,
                'https://meet.google.com/aed-dev', NULL,
                now(), now(), NULL)
        ON CONFLICT (id) DO NOTHING
    """), {"id": str(_SLOT), "t": str(_T), "mid": str(_MAT_AED),
           "cohid": str(_COHORTE), "fi": _SLOT_FECHAS[0]})
    print("  [ok]  SlotEncuentro AED (Lunes 18-20hs)")

    # 4 InstanciaEncuentro generadas por el slot
    for ins_id, fecha in zip(_INS_SLOT, _SLOT_FECHAS):
        await conn.execute(sa.text("""
            INSERT INTO instancia_encuentro
                (id, tenant_id, slot_id, materia_id, cohorte_id,
                 fecha, hora_inicio, hora_fin, titulo, estado,
                 meet_url, video_url, comentario, created_at, updated_at, deleted_at)
            VALUES (:id, :t, :slot, :mid, :cohid,
                    :fecha, '18:00', '20:00', 'Teórica AED', 'Programado',
                    'https://meet.google.com/aed-dev', NULL, NULL,
                    now(), now(), NULL)
            ON CONFLICT (id) DO NOTHING
        """), {"id": str(ins_id), "t": str(_T), "slot": str(_SLOT),
               "mid": str(_MAT_AED), "cohid": str(_COHORTE), "fecha": fecha})
    print(f"  [ok]  4 InstanciaEncuentro (slot AED): {_SLOT_FECHAS[0]} … {_SLOT_FECHAS[-1]}")

    # InstanciaEncuentro única: POO — Jueves 2026-07-09 19-21hs
    await conn.execute(sa.text("""
        INSERT INTO instancia_encuentro
            (id, tenant_id, slot_id, materia_id, cohorte_id,
             fecha, hora_inicio, hora_fin, titulo, estado,
             meet_url, video_url, comentario, created_at, updated_at, deleted_at)
        VALUES (:id, :t, NULL, :mid, :cohid,
                '2026-07-09', '19:00', '21:00', 'Práctica POO (único)', 'Programado',
                NULL, NULL, NULL,
                now(), now(), NULL)
        ON CONFLICT (id) DO NOTHING
    """), {"id": str(_INS_UNICA), "t": str(_T),
           "mid": str(_MAT_POO), "cohid": str(_COHORTE)})
    print("  [ok]  InstanciaEncuentro única POO (2026-07-09 19-21hs)")

    # Guardia: TUTOR en AED — Martes 2026-07-08 16-18hs
    await conn.execute(sa.text("""
        INSERT INTO guardia
            (id, tenant_id, tutor_id, materia_id, cohorte_id,
             fecha, hora_inicio, hora_fin, titulo, observaciones,
             created_at, updated_at, deleted_at)
        VALUES (:id, :t, :tid, :mid, :cohid,
                '2026-07-08', '16:00', '18:00', 'Guardia AED', NULL,
                now(), now(), NULL)
        ON CONFLICT (id) DO NOTHING
    """), {"id": str(_GUARDIA), "t": str(_T), "tid": str(tutor_id),
           "mid": str(_MAT_AED), "cohid": str(_COHORTE)})
    print("  [ok]  Guardia TUTOR en AED (2026-07-08 16-18hs)")

    for guardia in _build_professor_guardias(profesor_id):
        await conn.execute(sa.text("""
            INSERT INTO guardia
                (id, tenant_id, tutor_id, materia_id, cohorte_id,
                 fecha, hora_inicio, hora_fin, titulo, observaciones,
                 created_at, updated_at, deleted_at)
            VALUES (:id, :t, :tid, :mid, :cohid,
                    :fecha, :hora_inicio, :hora_fin, :titulo, :observaciones,
                    now(), now(), NULL)
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": str(guardia["id"]),
            "t": str(_T),
            "tid": str(guardia["tutor_id"]),
            "mid": str(guardia["materia_id"]),
            "cohid": str(guardia["cohorte_id"]),
            "fecha": guardia["fecha"],
            "hora_inicio": guardia["hora_inicio"],
            "hora_fin": guardia["hora_fin"],
            "titulo": guardia["titulo"],
            "observaciones": guardia["observaciones"],
        })
        print(f"  [ok]  Guardia PROFESOR {guardia['titulo']}")


async def _ensure_comunicaciones(conn: sa.ext.asyncio.AsyncConnection) -> None:
    print("\n=== Comunicaciones ===")
    destinatarios = [
        ("alumno3@dev.com", _COM_IDS[0], "Aviso de atraso — AED",
         "Estimado Carlos, te informamos que registrás un atraso en la materia AED. Por favor contactá al equipo docente."),
        ("alumno5@dev.com", _COM_IDS[1], "Aviso de atraso — AED",
         "Estimado Pedro, te informamos que no tenés calificación registrada en AED. Por favor regularizá tu situación."),
        # Uno ya enviado para testear el historial
        ("alumno2@dev.com", _COM_IDS[2], "Confirmación de nota — AED",
         "Estimada María, tu nota en AED ha sido registrada exitosamente."),
    ]

    for email, com_id, asunto, cuerpo in destinatarios:
        email_lower = email.lower()
        is_sent = (com_id == _COM_IDS[2])
        estado  = "Enviado" if is_sent else "Pendiente"
        lote    = None if is_sent else str(_LOTE_ID)
        env_at  = sa.text("now()") if is_sent else None

        # Build row programmatically to avoid SQL injection via f-strings
        row = await conn.execute(sa.text("""
            SELECT 1 FROM comunicacion WHERE id=:id
        """), {"id": str(com_id)})
        if row.fetchone():
            print(f"  [skip] Comunicación [{estado}] -> {email}")
            continue

        await conn.execute(sa.text("""
            INSERT INTO comunicacion
                (id, tenant_id, asunto, cuerpo, destinatario,
                 destinatario_hash, destinatario_enc,
                 estado, lote_id, error_detail, enviado_at, retry_count,
                 created_at, updated_at, deleted_at)
            VALUES
                (:id, :t, :asunto, :cuerpo, :dest,
                 :dhash, :denc,
                 :estado, :lote, NULL, :env_at, 0,
                 now(), now(), NULL)
        """), {
            "id": str(com_id), "t": str(_T),
            "asunto": asunto, "cuerpo": cuerpo,
            "dest": email_lower,
            "dhash": _ehash(email_lower),
            "denc": _enc(email_lower, "comunicacion.destinatario"),
            "estado": estado,
            "lote": lote,
            "env_at": _HOY if is_sent else None,
        })
        print(f"  [ok]  Comunicación [{estado}] -> {email}")


async def _ensure_mensajes_internos(
    conn: sa.ext.asyncio.AsyncConnection,
    profesor_id: UUID,
    coordinador_id: UUID,
    tutor_id: UUID,
) -> None:
    print("\n=== Mensajes internos PROFESOR ===")

    for mensaje in _build_professor_inbox_messages(profesor_id, coordinador_id, tutor_id):
        row = await conn.execute(
            sa.text("SELECT 1 FROM mensaje_interno WHERE id=:id"),
            {"id": str(mensaje["id"])},
        )
        if row.fetchone():
            print(f"  [skip] Mensaje interno {mensaje['id']}")
            continue

        await conn.execute(sa.text("""
            INSERT INTO mensaje_interno
                (id, tenant_id, asunto, cuerpo, remitente_id, destinatario_id,
                 hilo_id, padre_id, leido_at, created_at, updated_at, deleted_at)
            VALUES
                (:id, :t, :asunto, :cuerpo, :remitente_id, :destinatario_id,
                 :hilo_id, :padre_id, :leido_at, :created_at, :updated_at, NULL)
        """), {
            "id": str(mensaje["id"]),
            "t": str(_T),
            "asunto": mensaje["asunto"],
            "cuerpo": mensaje["cuerpo"],
            "remitente_id": str(mensaje["remitente_id"]),
            "destinatario_id": str(mensaje["destinatario_id"]),
            "hilo_id": str(mensaje["hilo_id"]),
            "padre_id": str(mensaje["padre_id"]) if mensaje["padre_id"] else None,
            "leido_at": mensaje["leido_at"],
            "created_at": mensaje["created_at"],
            "updated_at": mensaje["updated_at"],
        })
        print(
            f"  [ok]  Hilo {mensaje['hilo_id']} | "
            f"{mensaje['remitente_id']} -> {mensaje['destinatario_id']}"
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    url = os.environ["DATABASE_URL"]
    print(f"\nConectando a: {url}\n")
    engine = create_async_engine(url, echo=False)

    async with engine.begin() as conn:
        # Verificar que el tenant DEV existe
        tenant = (await conn.execute(
            sa.text("SELECT id FROM tenant WHERE id=:id"),
            {"id": str(_T)},
        )).fetchone()
        if not tenant:
            print("ERROR: tenant DEV no encontrado. Ejecutá seed_dev.py primero.")
            return

        # Obtener usuarios base
        profesor_id = await _get_user_id(conn, "profesor@dev.com")
        tutor_id    = await _get_user_id(conn, "tutor@dev.com")
        coordinador_id = await _get_user_id(conn, "coordinador@dev.com")

        if not profesor_id:
            print("ERROR: profesor@dev.com no encontrado. Ejecutá seed_dev.py primero.")
            return
        if not tutor_id:
            print("ERROR: tutor@dev.com no encontrado. Ejecutá seed_dev.py primero.")
            return
        if not coordinador_id:
            print("ERROR: coordinador@dev.com no encontrado. Ejecutá seed_dev.py primero.")
            return

        print(f"  profesor_id = {profesor_id}")
        print(f"  tutor_id    = {tutor_id}")
        print(f"  coordinador_id = {coordinador_id}")

        await _ensure_alumnos(conn)
        await _ensure_estructura(conn)
        await _ensure_asignaciones_contextuales(conn, profesor_id, tutor_id, coordinador_id)
        await _ensure_padron(conn, profesor_id)
        await _ensure_umbrales(conn)
        await _ensure_calificaciones(conn)
        await _ensure_encuentros(conn, tutor_id, profesor_id)
        await _ensure_comunicaciones(conn)
        await _ensure_mensajes_internos(conn, profesor_id, coordinador_id, tutor_id)

    await engine.dispose()

    print("\n" + "=" * 60)
    print("  DATOS DE DOMINIO CARGADOS - RESUMEN")
    print("=" * 60)
    print("  Carrera: TUP  |  Cohorte: 2026")
    print("  Materias: AED, POO, BD")
    print()
    print("  Alumnos (password: Admin123!):")
    print("    alumno1@dev.com  Juan Garcia      AED:8 (aprobado)     POO:7 (aprobado)")
    print("    alumno2@dev.com  Maria Lopez      AED:7 (aprobado)     POO:6 (aprobado)")
    print("    alumno3@dev.com  Carlos Martinez  AED:4 (DESAPROBADO)  POO:3 (DESAPROBADO)")
    print("    alumno4@dev.com  Ana Rodriguez    AED:9 (aprobado)     POO:8 (aprobado)")
    print("    alumno5@dev.com  Pedro Sanchez    AED:sin nota")
    print()
    print("  Encuentros:")
    print("    - SlotEncuentro AED: Lunes 18-20hs (07/07, 14/07, 21/07, 28/07)")
    print("    - Encuentro unico POO: Jueves 09/07 19-21hs")
    print("    - Guardia TUTOR AED: Martes 08/07 16-18hs")
    print("    - Guardias PROFESOR: AED 10/07 18:30hs | POO 16/07 19:00hs")
    print()
    print("  Comunicaciones:")
    print("    - 2 Pendiente en lote (Carlos y Pedro, alumnos atrasados AED)")
    print("    - 1 Enviado (historial)")
    print()
    print("  Inbox PROFESOR:")
    print(f"    - Hilo coordinacion: {_HILO_COORDINACION}")
    print(f"    - Hilo tutoria: {_HILO_TUTORIA}")
    print("    - Destinatarios utiles para redactar mensajes manuales: coordinador@dev.com y tutor@dev.com")
    print()


if __name__ == "__main__":
    asyncio.run(main())
