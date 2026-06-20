"""seed.py — Seed completo para demo de activia-trace.

Ejecuta seed_dev.py + seed_domain.py en orden correcto.
Es idempotente: se puede correr múltiples veces sin errores.

Uso:
    python backend/scripts/seed.py                  # local
    docker compose run --rm seed                    # Docker
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[2]
_backend_root = _repo_root / "backend"
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

# Defaults de entorno para dev local (Docker ya los tiene en .env)
_DEV_DEFAULTS: dict[str, str] = {
    "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:5433/activia_trace",
    "SECRET_KEY": "demo-secret-key-minimum-32-characters-long-activia",
    "ENCRYPTION_KEY": "01234567890123456789012345678901",
}
for _k, _v in _DEV_DEFAULTS.items():
    os.environ.setdefault(_k, _v)

# Import after env is set
from seed_dev import main as seed_dev_main  # noqa: E402
from seed_domain import main as seed_domain_main  # noqa: E402


async def run() -> None:
    print("=" * 60)
    print("  ACTIVIA-TRACE — SEED COMPLETO")
    print("=" * 60)

    print("\n>>> PASO 1: Tenant + Usuarios base (seed_dev)")
    print("-" * 60)
    await seed_dev_main()

    print("\n>>> PASO 2: Dominio académico (seed_domain)")
    print("-" * 60)
    await seed_domain_main()

    print("\n" + "=" * 60)
    print("  SEED COMPLETADO")
    print("=" * 60)
    print("\nCredenciales de acceso (password: Admin123!):")
    print("  admin@dev.com       → ADMIN")
    print("  coordinador@dev.com → COORDINADOR")
    print("  profesor@dev.com    → PROFESOR")
    print("  tutor@dev.com       → TUTOR")
    print("  alumno@dev.com      → ALUMNO")
    print("  finanzas@dev.com    → FINANZAS")
    print("  nexo@dev.com        → NEXO")
    print()
    print("URL frontend: http://localhost:3000")
    print("URL backend:  http://localhost:8000")
    print("URL API docs: http://localhost:8000/docs")
    print()


if __name__ == "__main__":
    asyncio.run(run())
