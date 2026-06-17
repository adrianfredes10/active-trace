"""create tareas tables

Revision ID: 014
Revises: 013
Create Date: 2026-06-17

C-16: tareas, comentarios_tarea.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "014"
down_revision: str | None = "013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

estado_tarea = postgresql.ENUM(
    "Pendiente",
    "En progreso",
    "Resuelta",
    "Cancelada",
    name="estado_tarea",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    postgresql.ENUM(
        "Pendiente", "En progreso", "Resuelta", "Cancelada", name="estado_tarea"
    ).create(bind, checkfirst=True)

    op.create_table(
        "tareas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("materia_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("asignado_a", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asignado_por", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("estado", estado_tarea, nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("contexto_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"]),
        sa.ForeignKeyConstraint(["asignado_a"], ["usuarios.id"]),
        sa.ForeignKeyConstraint(["asignado_por"], ["usuarios.id"]),
    )
    op.create_index("ix_tareas_tenant_id", "tareas", ["tenant_id"])
    op.create_index("ix_tareas_materia_id", "tareas", ["materia_id"])
    op.create_index("ix_tareas_asignado_a", "tareas", ["asignado_a"])
    op.create_index("ix_tareas_asignado_por", "tareas", ["asignado_por"])

    op.create_table(
        "comentarios_tarea",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tarea_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("autor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("creado_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["tarea_id"], ["tareas.id"]),
        sa.ForeignKeyConstraint(["autor_id"], ["usuarios.id"]),
    )
    op.create_index("ix_comentarios_tarea_tenant_id", "comentarios_tarea", ["tenant_id"])
    op.create_index("ix_comentarios_tarea_tarea_id", "comentarios_tarea", ["tarea_id"])


def downgrade() -> None:
    op.drop_table("comentarios_tarea")
    op.drop_table("tareas")
    bind = op.get_bind()
    postgresql.ENUM(name="estado_tarea").drop(bind, checkfirst=True)
