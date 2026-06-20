"""026: merge branches — main chain + profesor branch.

Merges the main chain (025_comunicacion_backfill_destinatario_enc) with the
profesor permissions branch (019_profesor_coloquios_ver) so all subsequent
migrations have a single head.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = "026_merge_heads"
down_revision: Union[str, tuple[str, ...], None] = (
    "025_comunicacion_backfill_destinatario_enc",
    "019_profesor_coloquios_ver",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
