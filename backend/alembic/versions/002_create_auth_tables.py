"""create auth tables

Revision ID: 002
Revises: 001
Create Date: 2026-06-12

Tablas de autenticación (C-03): usuarios (mínima), refresh_tokens,
password_reset_tokens. Convención: una migración por cambio de schema.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=512), nullable=False),
        sa.Column("email_hash", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("two_factor_enabled", sa.Boolean(), nullable=False),
        sa.Column("totp_secret", sa.String(length=512), nullable=True),
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
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id", "email_hash", name="uq_usuarios_tenant_email_hash"
        ),
    )
    op.create_index("ix_usuarios_tenant_id", "usuarios", ["tenant_id"])
    op.create_index("ix_usuarios_email_hash", "usuarios", ["email_hash"])

    for table in ("refresh_tokens", "password_reset_tokens"):
        op.create_table(
            table,
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("tenant_id", sa.Uuid(), nullable=False),
            sa.Column("usuario_id", sa.Uuid(), nullable=False),
            sa.Column("token_hash", sa.String(length=64), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
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
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
            sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("token_hash", name=f"uq_{table}_token_hash"),
        )
        op.create_index(f"ix_{table}_tenant_id", table, ["tenant_id"])
        op.create_index(f"ix_{table}_usuario_id", table, ["usuario_id"])
        op.create_index(f"ix_{table}_token_hash", table, ["token_hash"])

    # columna específica de cadena de rotación en refresh_tokens
    op.add_column(
        "refresh_tokens",
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "refresh_tokens",
        sa.Column("replaced_by_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_refresh_tokens_replaced_by",
        "refresh_tokens",
        "refresh_tokens",
        ["replaced_by_id"],
        ["id"],
    )
    # columna específica de un-solo-uso en password_reset_tokens
    op.add_column(
        "password_reset_tokens",
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("password_reset_tokens")
    op.drop_table("refresh_tokens")
    op.drop_table("usuarios")
