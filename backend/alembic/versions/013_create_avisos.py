"""create avisos tables

Revision ID: 013
Revises: 012
Create Date: 2026-06-17

C-15: avisos, acknowledgments_aviso.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "013"
down_revision: str | None = "012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

alcance_aviso = postgresql.ENUM(
    "Global",
    "PorMateria",
    "PorCohorte",
    "PorRol",
    name="alcance_aviso",
    create_type=False,
)
severidad_aviso = postgresql.ENUM(
    "Info",
    "Advertencia",
    "Crítico",
    name="severidad_aviso",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    postgresql.ENUM(
        "Global", "PorMateria", "PorCohorte", "PorRol", name="alcance_aviso"
    ).create(bind, checkfirst=True)
    postgresql.ENUM("Info", "Advertencia", "Crítico", name="severidad_aviso").create(
        bind, checkfirst=True
    )

    op.create_table(
        "avisos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("alcance", alcance_aviso, nullable=False),
        sa.Column("materia_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cohorte_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("rol_destino", sa.String(30), nullable=True),
        sa.Column("severidad", severidad_aviso, nullable=False),
        sa.Column("titulo", sa.String(200), nullable=False),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column("inicio_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fin_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("orden", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("requiere_ack", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"]),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohortes.id"]),
    )
    op.create_index("ix_avisos_tenant_id", "avisos", ["tenant_id"])
    op.create_index("ix_avisos_materia_id", "avisos", ["materia_id"])
    op.create_index("ix_avisos_cohorte_id", "avisos", ["cohorte_id"])

    op.create_table(
        "acknowledgments_aviso",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("aviso_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("confirmado_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["aviso_id"], ["avisos.id"]),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
        sa.UniqueConstraint(
            "tenant_id", "aviso_id", "usuario_id", name="uq_ack_aviso_usuario"
        ),
    )
    op.create_index(
        "ix_acknowledgments_aviso_tenant_id", "acknowledgments_aviso", ["tenant_id"]
    )
    op.create_index(
        "ix_acknowledgments_aviso_aviso_id", "acknowledgments_aviso", ["aviso_id"]
    )


def downgrade() -> None:
    op.drop_table("acknowledgments_aviso")
    op.drop_table("avisos")
    bind = op.get_bind()
    postgresql.ENUM(name="severidad_aviso").drop(bind, checkfirst=True)
    postgresql.ENUM(name="alcance_aviso").drop(bind, checkfirst=True)
