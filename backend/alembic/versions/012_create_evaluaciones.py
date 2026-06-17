"""create evaluaciones and coloquios tables

Revision ID: 012
Revises: 011
Create Date: 2026-06-17

C-14: evaluaciones, turnos, convocados, reservas, resultados.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "012"
down_revision: str | None = "011"
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
estado_evaluacion = postgresql.ENUM(
    "Abierta",
    "Cerrada",
    name="estado_evaluacion",
    create_type=False,
)
estado_reserva = postgresql.ENUM(
    "Activa",
    "Cancelada",
    name="estado_reserva_evaluacion",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    postgresql.ENUM(
        "Parcial", "TP", "Coloquio", "Recuperatorio", name="tipo_evaluacion"
    ).create(bind, checkfirst=True)
    postgresql.ENUM("Abierta", "Cerrada", name="estado_evaluacion").create(
        bind, checkfirst=True
    )
    postgresql.ENUM("Activa", "Cancelada", name="estado_reserva_evaluacion").create(
        bind, checkfirst=True
    )

    op.create_table(
        "evaluaciones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("materia_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cohorte_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tipo", tipo_evaluacion, nullable=False),
        sa.Column("instancia", sa.String(200), nullable=False),
        sa.Column("estado", estado_evaluacion, nullable=False),
        sa.Column("dias_disponibles", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"]),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohortes.id"]),
    )
    op.create_index("ix_evaluaciones_tenant_id", "evaluaciones", ["tenant_id"])
    op.create_index("ix_evaluaciones_materia_id", "evaluaciones", ["materia_id"])
    op.create_index("ix_evaluaciones_cohorte_id", "evaluaciones", ["cohorte_id"])

    op.create_table(
        "turnos_evaluacion",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evaluacion_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("hora", sa.Time(), nullable=False),
        sa.Column("cupo_max", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["evaluacion_id"], ["evaluaciones.id"]),
    )
    op.create_index("ix_turnos_evaluacion_tenant_id", "turnos_evaluacion", ["tenant_id"])
    op.create_index(
        "ix_turnos_evaluacion_evaluacion_id", "turnos_evaluacion", ["evaluacion_id"]
    )

    op.create_table(
        "convocados_evaluacion",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evaluacion_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("alumno_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["evaluacion_id"], ["evaluaciones.id"]),
        sa.ForeignKeyConstraint(["alumno_id"], ["usuarios.id"]),
        sa.UniqueConstraint(
            "tenant_id", "evaluacion_id", "alumno_id", name="uq_convocado_evaluacion_alumno"
        ),
    )
    op.create_index(
        "ix_convocados_evaluacion_tenant_id", "convocados_evaluacion", ["tenant_id"]
    )
    op.create_index(
        "ix_convocados_evaluacion_evaluacion_id",
        "convocados_evaluacion",
        ["evaluacion_id"],
    )

    op.create_table(
        "reservas_evaluacion",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evaluacion_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("turno_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("alumno_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fecha_hora", sa.DateTime(timezone=True), nullable=False),
        sa.Column("estado", estado_reserva, nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["evaluacion_id"], ["evaluaciones.id"]),
        sa.ForeignKeyConstraint(["turno_id"], ["turnos_evaluacion.id"]),
        sa.ForeignKeyConstraint(["alumno_id"], ["usuarios.id"]),
    )
    op.create_index("ix_reservas_evaluacion_tenant_id", "reservas_evaluacion", ["tenant_id"])
    op.create_index(
        "ix_reservas_evaluacion_evaluacion_id", "reservas_evaluacion", ["evaluacion_id"]
    )
    op.create_index("ix_reservas_evaluacion_turno_id", "reservas_evaluacion", ["turno_id"])

    op.create_table(
        "resultados_evaluacion",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evaluacion_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("alumno_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nota_final", sa.String(50), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["evaluacion_id"], ["evaluaciones.id"]),
        sa.ForeignKeyConstraint(["alumno_id"], ["usuarios.id"]),
        sa.UniqueConstraint(
            "tenant_id",
            "evaluacion_id",
            "alumno_id",
            name="uq_resultado_evaluacion_alumno",
        ),
    )
    op.create_index(
        "ix_resultados_evaluacion_tenant_id", "resultados_evaluacion", ["tenant_id"]
    )
    op.create_index(
        "ix_resultados_evaluacion_evaluacion_id",
        "resultados_evaluacion",
        ["evaluacion_id"],
    )


def downgrade() -> None:
    op.drop_table("resultados_evaluacion")
    op.drop_table("reservas_evaluacion")
    op.drop_table("convocados_evaluacion")
    op.drop_table("turnos_evaluacion")
    op.drop_table("evaluaciones")
    bind = op.get_bind()
    postgresql.ENUM(name="estado_reserva_evaluacion").drop(bind, checkfirst=True)
    postgresql.ENUM(name="estado_evaluacion").drop(bind, checkfirst=True)
    postgresql.ENUM(name="tipo_evaluacion").drop(bind, checkfirst=True)
