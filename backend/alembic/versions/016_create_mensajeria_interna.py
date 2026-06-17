"""create mensajeria interna tables

Revision ID: 016
Revises: 015
Create Date: 2026-06-17

C-20: hilos_mensaje, mensajes_internos.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "016"
down_revision: str | None = "015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "hilos_mensaje",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("asunto", sa.String(200), nullable=False),
        sa.Column("participante_a_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("participante_b_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("iniciado_por_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ultimo_mensaje_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["participante_a_id"], ["usuarios.id"]),
        sa.ForeignKeyConstraint(["participante_b_id"], ["usuarios.id"]),
        sa.ForeignKeyConstraint(["iniciado_por_id"], ["usuarios.id"]),
    )
    op.create_index("ix_hilos_mensaje_tenant_id", "hilos_mensaje", ["tenant_id"])
    op.create_index(
        "ix_hilos_mensaje_participante_a_id", "hilos_mensaje", ["participante_a_id"]
    )
    op.create_index(
        "ix_hilos_mensaje_participante_b_id", "hilos_mensaje", ["participante_b_id"]
    )

    op.create_table(
        "mensajes_internos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("hilo_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("autor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column("enviado_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["hilo_id"], ["hilos_mensaje.id"]),
        sa.ForeignKeyConstraint(["autor_id"], ["usuarios.id"]),
    )
    op.create_index("ix_mensajes_internos_tenant_id", "mensajes_internos", ["tenant_id"])
    op.create_index("ix_mensajes_internos_hilo_id", "mensajes_internos", ["hilo_id"])
    op.create_index("ix_mensajes_internos_autor_id", "mensajes_internos", ["autor_id"])


def downgrade() -> None:
    op.drop_table("mensajes_internos")
    op.drop_table("hilos_mensaje")
