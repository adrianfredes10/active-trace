"""create audit_logs (append-only)

Revision ID: 004
Revises: 003
Create Date: 2026-06-12

E-AUD (C-05): audit_logs inmutable con trigger que rechaza UPDATE/DELETE.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column(
            "fecha_hora",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("impersonado_id", sa.Uuid(), nullable=True),
        sa.Column("materia_id", sa.Uuid(), nullable=True),
        sa.Column("accion", sa.String(length=80), nullable=False),
        sa.Column("detalle", JSONB(), nullable=True),
        sa.Column("filas_afectadas", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ip", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["actor_id"], ["usuarios.id"]),
        sa.ForeignKeyConstraint(["impersonado_id"], ["usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_tenant_id", "audit_logs", ["tenant_id"])
    op.create_index("ix_audit_logs_fecha_hora", "audit_logs", ["fecha_hora"])
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])
    op.create_index("ix_audit_logs_accion", "audit_logs", ["accion"])

    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_audit_log_mutation()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'audit_logs is append-only';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_logs_no_update
        BEFORE UPDATE OR DELETE ON audit_logs
        FOR EACH ROW EXECUTE FUNCTION prevent_audit_log_mutation();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS audit_logs_no_update ON audit_logs")
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_log_mutation()")
    op.drop_table("audit_logs")
