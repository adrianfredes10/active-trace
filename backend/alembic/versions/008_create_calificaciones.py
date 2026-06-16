"""create calificaciones and umbrales_materia tables

Revision ID: 008
Revises: 007
Create Date: 2026-06-16

C-10: calificaciones + umbrales_materia.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "008"
down_revision: str | None = "007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

origen_calificacion = postgresql.ENUM(
    "Importado",
    "Manual",
    name="origen_calificacion",
    create_type=False,
)


def upgrade() -> None:
    postgresql.ENUM("Importado", "Manual", name="origen_calificacion").create(
        op.get_bind(), checkfirst=True
    )

    op.create_table(
        "umbrales_materia",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("asignacion_id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column("umbral_pct", sa.Integer(), nullable=False, server_default="60"),
        sa.Column(
            "valores_aprobatorios",
            postgresql.JSONB(),
            nullable=False,
            server_default='["Satisfactorio", "Supera lo esperado"]',
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
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["asignacion_id"], ["asignaciones.id"]),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("asignacion_id", name="uq_umbrales_materia_asignacion"),
    )
    op.create_index("ix_umbrales_materia_tenant_id", "umbrales_materia", ["tenant_id"])
    op.create_index("ix_umbrales_materia_materia_id", "umbrales_materia", ["materia_id"])

    op.create_table(
        "calificaciones",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("asignacion_id", sa.Uuid(), nullable=False),
        sa.Column("entrada_padron_id", sa.Uuid(), nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=False),
        sa.Column("actividad", sa.String(length=255), nullable=False),
        sa.Column("nota_numerica", sa.Numeric(6, 2), nullable=True),
        sa.Column("nota_textual", sa.String(length=100), nullable=True),
        sa.Column("aprobado", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "origen",
            origen_calificacion,
            nullable=False,
            server_default="Importado",
        ),
        sa.Column(
            "importado_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
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
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["asignacion_id"], ["asignaciones.id"]),
        sa.ForeignKeyConstraint(["entrada_padron_id"], ["entradas_padron.id"]),
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "asignacion_id",
            "entrada_padron_id",
            "actividad",
            name="uq_calificaciones_asignacion_entrada_actividad",
        ),
    )
    op.create_index("ix_calificaciones_tenant_id", "calificaciones", ["tenant_id"])
    op.create_index("ix_calificaciones_asignacion_id", "calificaciones", ["asignacion_id"])
    op.create_index("ix_calificaciones_materia_id", "calificaciones", ["materia_id"])
    op.create_index(
        "ix_calificaciones_entrada_padron_id", "calificaciones", ["entrada_padron_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_calificaciones_entrada_padron_id", table_name="calificaciones")
    op.drop_index("ix_calificaciones_materia_id", table_name="calificaciones")
    op.drop_index("ix_calificaciones_asignacion_id", table_name="calificaciones")
    op.drop_index("ix_calificaciones_tenant_id", table_name="calificaciones")
    op.drop_table("calificaciones")
    op.drop_index("ix_umbrales_materia_materia_id", table_name="umbrales_materia")
    op.drop_index("ix_umbrales_materia_tenant_id", table_name="umbrales_materia")
    op.drop_table("umbrales_materia")
    postgresql.ENUM(name="origen_calificacion").drop(op.get_bind(), checkfirst=True)
