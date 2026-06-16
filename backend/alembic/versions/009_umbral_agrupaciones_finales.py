"""add agrupaciones_finales to umbrales_materia

Revision ID: 009
Revises: 008
Create Date: 2026-06-16

C-11: agrupaciones para notas finales (F2.5).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "009"
down_revision: str | None = "008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "umbrales_materia",
        sa.Column(
            "agrupaciones_finales",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
    )


def downgrade() -> None:
    op.drop_column("umbrales_materia", "agrupaciones_finales")
