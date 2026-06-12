"""create estructura academica tables

Revision ID: 005
Revises: 004
Create Date: 2026-06-12

Tablas C-06: carreras, cohortes, materias.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

entidad_estado = postgresql.ENUM(
    "Activa",
    "Inactiva",
    name="entidad_estado",
    create_type=False,
)


def upgrade() -> None:
    postgresql.ENUM("Activa", "Inactiva", name="entidad_estado").create(
        op.get_bind(),
        checkfirst=True,
    )

    op.create_table(
        "carreras",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("codigo", sa.String(length=50), nullable=False),
        sa.Column("nombre", sa.String(length=255), nullable=False),
        sa.Column(
            "estado",
            entidad_estado,
            nullable=False,
            server_default="Activa",
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "codigo", name="uq_carreras_tenant_codigo"),
    )
    op.create_index("ix_carreras_tenant_id", "carreras", ["tenant_id"])

    op.create_table(
        "cohortes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("carrera_id", sa.Uuid(), nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("anio", sa.Integer(), nullable=False),
        sa.Column("vig_desde", sa.Date(), nullable=False),
        sa.Column("vig_hasta", sa.Date(), nullable=True),
        sa.Column(
            "estado",
            entidad_estado,
            nullable=False,
            server_default="Activa",
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
        sa.ForeignKeyConstraint(["carrera_id"], ["carreras.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "carrera_id",
            "nombre",
            name="uq_cohortes_tenant_carrera_nombre",
        ),
    )
    op.create_index("ix_cohortes_tenant_id", "cohortes", ["tenant_id"])
    op.create_index("ix_cohortes_carrera_id", "cohortes", ["carrera_id"])

    op.create_table(
        "materias",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("codigo", sa.String(length=50), nullable=False),
        sa.Column("nombre", sa.String(length=255), nullable=False),
        sa.Column(
            "estado",
            entidad_estado,
            nullable=False,
            server_default="Activa",
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "codigo", name="uq_materias_tenant_codigo"),
    )
    op.create_index("ix_materias_tenant_id", "materias", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_materias_tenant_id", table_name="materias")
    op.drop_table("materias")
    op.drop_index("ix_cohortes_carrera_id", table_name="cohortes")
    op.drop_index("ix_cohortes_tenant_id", table_name="cohortes")
    op.drop_table("cohortes")
    op.drop_index("ix_carreras_tenant_id", table_name="carreras")
    op.drop_table("carreras")
    postgresql.ENUM(name="entidad_estado").drop(op.get_bind(), checkfirst=True)
