"""create encuentros and guardias tables

Revision ID: 011
Revises: 010
Create Date: 2026-06-17

C-13: slots_encuentro, instancias_encuentro, guardias.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "011"
down_revision: str | None = "010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

dia_semana = postgresql.ENUM(
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo",
    name="dia_semana",
    create_type=False,
)
estado_instancia = postgresql.ENUM(
    "Programado",
    "Realizado",
    "Cancelado",
    name="estado_instancia_encuentro",
    create_type=False,
)
estado_guardia = postgresql.ENUM(
    "Pendiente",
    "Realizada",
    "Cancelada",
    name="estado_guardia",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    postgresql.ENUM(
        "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo",
        name="dia_semana",
    ).create(bind, checkfirst=True)
    postgresql.ENUM(
        "Programado", "Realizado", "Cancelado", name="estado_instancia_encuentro"
    ).create(bind, checkfirst=True)
    postgresql.ENUM(
        "Pendiente", "Realizada", "Cancelada", name="estado_guardia"
    ).create(bind, checkfirst=True)

    op.create_table(
        "slots_encuentro",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("asignacion_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("materia_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("titulo", sa.String(200), nullable=False),
        sa.Column("hora", sa.Time(), nullable=False),
        sa.Column("dia_semana", dia_semana, nullable=True),
        sa.Column("fecha_inicio", sa.Date(), nullable=True),
        sa.Column("cant_semanas", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fecha_unica", sa.Date(), nullable=True),
        sa.Column("meet_url", sa.String(500), nullable=True),
        sa.Column("vig_desde", sa.Date(), nullable=False),
        sa.Column("vig_hasta", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["asignacion_id"], ["asignaciones.id"]),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"]),
    )

    op.create_table(
        "instancias_encuentro",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("slot_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("materia_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("hora", sa.Time(), nullable=False),
        sa.Column("titulo", sa.String(200), nullable=False),
        sa.Column(
            "estado",
            estado_instancia,
            nullable=False,
            server_default="Programado",
        ),
        sa.Column("meet_url", sa.String(500), nullable=True),
        sa.Column("video_url", sa.String(500), nullable=True),
        sa.Column("comentario", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["slot_id"], ["slots_encuentro.id"]),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"]),
    )

    op.create_table(
        "guardias",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("asignacion_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("materia_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("carrera_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cohorte_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dia", dia_semana, nullable=False),
        sa.Column("horario", sa.String(50), nullable=False),
        sa.Column(
            "estado",
            estado_guardia,
            nullable=False,
            server_default="Pendiente",
        ),
        sa.Column("comentarios", sa.Text(), nullable=True),
        sa.Column("creada_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["asignacion_id"], ["asignaciones.id"]),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"]),
        sa.ForeignKeyConstraint(["carrera_id"], ["carreras.id"]),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohortes.id"]),
    )


def downgrade() -> None:
    op.drop_table("guardias")
    op.drop_table("instancias_encuentro")
    op.drop_table("slots_encuentro")
    bind = op.get_bind()
    postgresql.ENUM(name="estado_guardia").drop(bind, checkfirst=True)
    postgresql.ENUM(name="estado_instancia_encuentro").drop(bind, checkfirst=True)
    postgresql.ENUM(name="dia_semana").drop(bind, checkfirst=True)
