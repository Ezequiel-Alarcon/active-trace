"""014: add actividades to version_padron (C-11).

Run order:
    alembic upgrade head
    alembic downgrade -1
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = "014_analisis_actividades"
down_revision: Union[str, None] = "013_analisis_reportes_permissions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "version_padron",
        op.Column("actividades", op.JSON(), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_column("version_padron", "actividades")