"""create comunicaciones table and tenant approval config

Revision ID: 010
Revises: 009
Create Date: 2026-06-17

C-12: cola de comunicaciones + aprobación masiva por tenant.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "010"
down_revision: str | None = "009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

estado_comunicacion = postgresql.ENUM(
    "Pendiente",
    "Enviando",
    "Enviado",
    "Error",
    "Cancelado",
    name="estado_comunicacion",
    create_type=False,
)


def upgrade() -> None:
    postgresql.ENUM(
        "Pendiente",
        "Enviando",
        "Enviado",
        "Error",
        "Cancelado",
        name="estado_comunicacion",
    ).create(op.get_bind(), checkfirst=True)

    op.add_column(
        "tenants",
        sa.Column(
            "aprobacion_masiva_comunicaciones",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )

    op.create_table(
        "comunicaciones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("enviado_por", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("materia_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("destinatario", sa.String(512), nullable=False),
        sa.Column("asunto", sa.String(255), nullable=False),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column(
            "estado",
            estado_comunicacion,
            nullable=False,
            server_default="Pendiente",
        ),
        sa.Column("lote_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("es_masivo", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("aprobado", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("aprobado_por", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("aprobado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("enviado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_detalle", sa.String(500), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["enviado_por"], ["usuarios.id"]),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"]),
        sa.ForeignKeyConstraint(["aprobado_por"], ["usuarios.id"]),
    )
    op.create_index("ix_comunicaciones_tenant_id", "comunicaciones", ["tenant_id"])
    op.create_index("ix_comunicaciones_lote_id", "comunicaciones", ["lote_id"])
    op.create_index("ix_comunicaciones_estado", "comunicaciones", ["estado"])
    op.create_index(
        "ix_comunicaciones_enviado_por", "comunicaciones", ["enviado_por"]
    )


def downgrade() -> None:
    op.drop_index("ix_comunicaciones_enviado_por", table_name="comunicaciones")
    op.drop_index("ix_comunicaciones_estado", table_name="comunicaciones")
    op.drop_index("ix_comunicaciones_lote_id", table_name="comunicaciones")
    op.drop_index("ix_comunicaciones_tenant_id", table_name="comunicaciones")
    op.drop_table("comunicaciones")
    op.drop_column("tenants", "aprobacion_masiva_comunicaciones")
    postgresql.ENUM(name="estado_comunicacion").drop(op.get_bind(), checkfirst=True)
