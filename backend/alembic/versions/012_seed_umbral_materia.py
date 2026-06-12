"""012: seed default umbral_materia (C-10).

Creates default umbral (umbral_pct=60, conjunto_aprobado=["A","B+","C","7","8","9","10"])
for all existing materias with asignacion_id=null.

Run order:
    alembic upgrade head
    alembic downgrade -1
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = "012_seed_umbral_materia"
down_revision: Union[str, None] = "011_umbral_materia"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DEFAULT_CONJUNTO = '["A","B+","C","7","8","9","10"]'


def upgrade() -> None:
    op.execute(f"""
        INSERT INTO umbral_materia (id, tenant_id, materia_id, asignacion_id, umbral_pct, conjunto_aprobado, created_at, updated_at, deleted_at)
        SELECT
            gen_random_uuid(),
            tenant_id,
            id AS materia_id,
            NULL::uuid AS asignacion_id,
            60 AS umbral_pct,
            '{DEFAULT_CONJUNTO}'::jsonb,
            now(),
            now(),
            NULL
        FROM materia
        WHERE deleted_at IS NULL
        ON CONFLICT (materia_id, asignacion_id, deleted_at) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DELETE FROM umbral_materia WHERE asignacion_id IS NULL")