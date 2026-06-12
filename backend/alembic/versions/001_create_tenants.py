"""create tenants

Revision ID: 001
Revises:
Create Date: 2026-06-12

Primera migración de dominio: crea la tabla raíz `tenants`.
Convención: una migración por cambio de schema.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("nombre", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column(
            "estado",
            sa.Enum("ACTIVO", "INACTIVO", name="tenant_estado"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_tenants_slug"),
    )


def downgrade() -> None:
    op.drop_table("tenants")
    sa.Enum(name="tenant_estado").drop(op.get_bind(), checkfirst=True)
