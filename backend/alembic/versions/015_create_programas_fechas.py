"""create programas and fechas academicas tables

Revision ID: 015
Revises: 014
Create Date: 2026-06-17

C-17: programas_materia, fechas_academicas.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "015"
down_revision: str | None = "014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

tipo_evaluacion = postgresql.ENUM(
    "Parcial",
    "TP",
    "Coloquio",
    "Recuperatorio",
    name="tipo_evaluacion",
    create_type=False,
)


def upgrade() -> None:
    op.create_table(
        "programas_materia",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("materia_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("carrera_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cohorte_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("titulo", sa.String(200), nullable=False),
        sa.Column("referencia_archivo", sa.String(500), nullable=False),
        sa.Column("cargado_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"]),
        sa.ForeignKeyConstraint(["carrera_id"], ["carreras.id"]),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohortes.id"]),
        sa.UniqueConstraint(
            "tenant_id",
            "materia_id",
            "carrera_id",
            "cohorte_id",
            name="uq_programa_materia_carrera_cohorte",
        ),
    )
    op.create_index("ix_programas_materia_tenant_id", "programas_materia", ["tenant_id"])
    op.create_index("ix_programas_materia_materia_id", "programas_materia", ["materia_id"])

    op.create_table(
        "fechas_academicas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("materia_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cohorte_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tipo", tipo_evaluacion, nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("periodo", sa.String(20), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("titulo", sa.String(200), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"]),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohortes.id"]),
    )
    op.create_index("ix_fechas_academicas_tenant_id", "fechas_academicas", ["tenant_id"])
    op.create_index(
        "ix_fechas_academicas_materia_id", "fechas_academicas", ["materia_id"]
    )
    op.create_index(
        "ix_fechas_academicas_cohorte_id", "fechas_academicas", ["cohorte_id"]
    )


def downgrade() -> None:
    op.drop_table("fechas_academicas")
    op.drop_table("programas_materia")
