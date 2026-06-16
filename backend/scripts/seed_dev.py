"""seed_dev.py — Crea datos de desarrollo para activia-trace.

Crea:
  - 1 tenant de dev (codigo="DEV")
  - 7 roles con sus permisos (segun GLOBAL_TENANT_ID del RBAC, ya presentes)
  - 1 usuario (Usuario + AuthUser) por rol con credenciales simples

Uso:
    python backend/scripts/seed_dev.py

El script es IDEMPOTENTE: se puede correr multiples veces sin errores.

Requiere las siguientes variables de entorno (o archivo .env en backend/):
    DATABASE_URL
    SECRET_KEY
    ENCRYPTION_KEY  (exactamente 32 bytes)

Para un entorno local rapido, puede sobreescribir esas variables en el
bloque DEV_DEFAULTS que esta al inicio de main().
"""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import date
from pathlib import Path
from uuid import UUID, uuid4

# ---------------------------------------------------------------------------
# Asegurar que el package backend/app sea importable desde cualquier CWD.
# ---------------------------------------------------------------------------
_repo_root = Path(__file__).resolve().parents[2]  # active-trace/
_backend_root = _repo_root / "backend"
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

# ---------------------------------------------------------------------------
# Defaults de entorno para dev (si no estan seteados externamente).
# ---------------------------------------------------------------------------
_DEV_ENV_DEFAULTS: dict[str, str] = {
    "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:5432/activia_trace_test",
    "SECRET_KEY": "dev-secret-key-minimum-32-characters-long",
    "ENCRYPTION_KEY": "01234567890123456789012345678901",  # exactamente 32 bytes
}

for _k, _v in _DEV_ENV_DEFAULTS.items():
    os.environ.setdefault(_k, _v)

# ---------------------------------------------------------------------------
# Imports del proyecto (despues de setear el entorno).
# ---------------------------------------------------------------------------
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.security.crypto import encrypt
from app.core.security.hashing import hash_email_for_search
from app.core.security.passwords import hash_password
from app.rbac.constants import GLOBAL_TENANT_ID

# ---------------------------------------------------------------------------
# Constantes de dev
# ---------------------------------------------------------------------------

_DEV_TENANT_ID = UUID("11111111-2222-3333-4444-555555555555")
_DEV_TENANT_CODIGO = "DEV"
_DEV_TENANT_NOMBRE = "Tenant de Desarrollo"

# UUIDs fijos para los roles globales (de 004_rbac_tables.py)
_ROL_IDS: dict[str, UUID] = {
    "ALUMNO":      UUID("00000000-0000-0000-0000-a00000000001"),
    "TUTOR":       UUID("00000000-0000-0000-0000-a00000000002"),
    "PROFESOR":    UUID("00000000-0000-0000-0000-a00000000003"),
    "COORDINADOR": UUID("00000000-0000-0000-0000-a00000000004"),
    "NEXO":        UUID("00000000-0000-0000-0000-a00000000005"),
    "ADMIN":       UUID("00000000-0000-0000-0000-a00000000006"),
    "FINANZAS":    UUID("00000000-0000-0000-0000-a00000000007"),
}

_PLAINTEXT_PASSWORD = "Admin123!"

# (email, nombre, apellidos, rol_nombre)
_USERS: list[tuple[str, str, str, str]] = [
    ("admin@dev.com",       "Admin",       "Dev",         "ADMIN"),
    ("finanzas@dev.com",    "Finanzas",    "Dev",         "FINANZAS"),
    ("coordinador@dev.com", "Coordinador", "Dev",         "COORDINADOR"),
    ("profesor@dev.com",    "Profesor",    "Dev",         "PROFESOR"),
    ("tutor@dev.com",       "Tutor",       "Dev",         "TUTOR"),
    ("nexo@dev.com",        "Nexo",        "Dev",         "NEXO"),
    ("alumno@dev.com",      "Alumno",      "Dev",         "ALUMNO"),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _encrypt_pii(plaintext: str, tenant_id: UUID, aad_suffix: str) -> str:
    """Cifra un campo PII con AES-256-GCM usando la clave del entorno."""
    return encrypt(plaintext, tenant_id=tenant_id, aad_suffix=aad_suffix)


# ---------------------------------------------------------------------------
# Seed steps
# ---------------------------------------------------------------------------

async def _ensure_dev_tenant(conn: sa.ext.asyncio.AsyncConnection) -> None:
    """Inserta el tenant DEV si no existe."""
    await conn.execute(
        sa.text("""
            INSERT INTO tenant (id, codigo, nombre, estado, created_at, updated_at, deleted_at, umbral_aprobacion)
            VALUES (:id, :codigo, :nombre, 'Activo', now(), now(), NULL, 10)
            ON CONFLICT (id) DO NOTHING
        """),
        {
            "id": str(_DEV_TENANT_ID),
            "codigo": _DEV_TENANT_CODIGO,
            "nombre": _DEV_TENANT_NOMBRE,
        },
    )
    print(f"  [tenant] {_DEV_TENANT_CODIGO} — {_DEV_TENANT_NOMBRE}  (id={_DEV_TENANT_ID})")


async def _ensure_user(
    conn: sa.ext.asyncio.AsyncConnection,
    email: str,
    nombre: str,
    apellidos: str,
    rol_nombre: str,
    tenant_id: UUID,
) -> None:
    """Inserta AuthUser + Usuario + Asignacion si el email aun no existe."""
    email_lower = email.lower()
    email_hash = hash_email_for_search(email_lower, tenant_id)

    # ---------- AuthUser ----------
    # Verificar si ya existe por email_hash en este tenant
    row = (await conn.execute(
        sa.text("""
            SELECT id FROM auth_user
            WHERE tenant_id = :tid AND email_hash = :hash AND deleted_at IS NULL
        """),
        {"tid": str(tenant_id), "hash": email_hash},
    )).fetchone()

    if row:
        auth_user_id = UUID(str(row[0]))
        print(f"  [skip]  {email} ya existe (auth_user.id={auth_user_id})")
    else:
        auth_user_id = uuid4()
        email_enc = _encrypt_pii(email_lower, tenant_id, aad_suffix="email")
        pw_hash = hash_password(_PLAINTEXT_PASSWORD)

        await conn.execute(
            sa.text("""
                INSERT INTO auth_user
                    (id, tenant_id, email_enc, email_hash, password_hash,
                     totp_secret_enc, totp_enabled, is_active,
                     failed_login_count, last_login_at,
                     created_at, updated_at, deleted_at)
                VALUES
                    (:id, :tid, :email_enc, :email_hash, :pw_hash,
                     NULL, false, true,
                     0, NULL,
                     now(), now(), NULL)
                ON CONFLICT (id) DO NOTHING
            """),
            {
                "id": str(auth_user_id),
                "tid": str(tenant_id),
                "email_enc": email_enc,
                "email_hash": email_hash,
                "pw_hash": pw_hash,
            },
        )

        # ---------- Usuario (mismo UUID, PII cifrada) ----------
        dni_placeholder = _encrypt_pii("00000000", tenant_id, aad_suffix="dni")
        cuil_placeholder = _encrypt_pii("20000000009", tenant_id, aad_suffix="cuil")
        cbu_placeholder = _encrypt_pii("0000000000000000000000", tenant_id, aad_suffix="cbu")

        await conn.execute(
            sa.text("""
                INSERT INTO usuario
                    (id, tenant_id, email_hash, email_enc,
                     dni_enc, cuil_enc, cbu_enc, alias_cbu_enc,
                     nombre, apellidos,
                     banco, regional, legajo, legajo_profesional,
                     fecha_nacimiento, genero, observaciones,
                     created_at, updated_at, deleted_at)
                VALUES
                    (:id, :tid, :email_hash, :email_enc,
                     :dni_enc, :cuil_enc, :cbu_enc, NULL,
                     :nombre, :apellidos,
                     NULL, NULL, NULL, NULL,
                     NULL, NULL, NULL,
                     now(), now(), NULL)
                ON CONFLICT (tenant_id, email_hash) DO NOTHING
            """),
            {
                "id": str(auth_user_id),
                "tid": str(tenant_id),
                "email_hash": email_hash,
                "email_enc": email_enc,
                "dni_enc": dni_placeholder,
                "cuil_enc": cuil_placeholder,
                "cbu_enc": cbu_placeholder,
                "nombre": nombre,
                "apellidos": apellidos,
            },
        )
        print(f"  [ok]    {email}  ({nombre} {apellidos})  id={auth_user_id}")

    # ---------- Asignacion usuario → rol (contexto Global) ----------
    # asignacion no tiene unique constraint sobre (tenant_id, usuario_id, rol_id),
    # por eso chequeamos primero en vez de usar ON CONFLICT DO NOTHING.
    rol_id = _ROL_IDS[rol_nombre]
    existing_asig = (await conn.execute(
        sa.text("""
            SELECT id FROM asignacion
            WHERE tenant_id = :tid
              AND usuario_id = :uid
              AND rol_id = :rid
              AND deleted_at IS NULL
        """),
        {"tid": str(tenant_id), "uid": str(auth_user_id), "rid": str(rol_id)},
    )).fetchone()

    if not existing_asig:
        asignacion_id = uuid4()
        await conn.execute(
            sa.text("""
                INSERT INTO asignacion
                    (id, tenant_id, usuario_id, rol_id,
                     contexto_tipo, contexto_id, responsable_id,
                     desde, hasta,
                     created_at, updated_at, deleted_at)
                VALUES
                    (:id, :tid, :uid, :rid,
                     'Global', NULL, NULL,
                     :desde, NULL,
                     now(), now(), NULL)
            """),
            {
                "id": str(asignacion_id),
                "tid": str(tenant_id),
                "uid": str(auth_user_id),
                "rid": str(rol_id),
                "desde": date.today(),
            },
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    database_url = os.environ["DATABASE_URL"]
    print(f"\nConectando a: {database_url}\n")

    engine = create_async_engine(database_url, echo=False)

    async with engine.begin() as conn:
        print("=== Tenant ===")
        await _ensure_dev_tenant(conn)

        print("\n=== Usuarios y asignaciones ===")
        for email, nombre, apellidos, rol in _USERS:
            await _ensure_user(
                conn,
                email=email,
                nombre=nombre,
                apellidos=apellidos,
                rol_nombre=rol,
                tenant_id=_DEV_TENANT_ID,
            )

    await engine.dispose()

    # ---------- Tabla de credenciales ----------
    col_email = 30
    col_pw    = 12
    col_rol   = 14
    sep = f"+{'-' * (col_email + 2)}+{'-' * (col_pw + 2)}+{'-' * (col_rol + 2)}+"
    header = (
        f"| {'EMAIL':<{col_email}} | {'PASSWORD':<{col_pw}} | {'ROL':<{col_rol}} |"
    )

    print("\n")
    print("=" * len(sep))
    print("  CREDENCIALES DE DESARROLLO")
    print("=" * len(sep))
    print(sep)
    print(header)
    print(sep)
    for email, _, _, rol in _USERS:
        print(f"| {email:<{col_email}} | {_PLAINTEXT_PASSWORD:<{col_pw}} | {rol:<{col_rol}} |")
    print(sep)
    print(f"\nTenant DEV id : {_DEV_TENANT_ID}")
    print(f"Tenant codigo : {_DEV_TENANT_CODIGO}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
