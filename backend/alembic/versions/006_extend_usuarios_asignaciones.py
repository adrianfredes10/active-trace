"""extend usuarios with PII fields and create asignaciones table

Revision ID: 006
Revises: 005
Create Date: 2026-06-16

C-07: ALTER TABLE usuarios (campos de negocio + PII cifrada);
      CREATE TYPE usuario_estado; CREATE TYPE rol_asignacion;
      CREATE TABLE asignaciones.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006"
down_revision: str | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

usuario_estado = postgresql.ENUM(
    "Activo",
    "Inactivo",
    name="usuario_estado",
    create_type=False,
)

rol_asignacion = postgresql.ENUM(
    "ALUMNO",
    "TUTOR",
    "PROFESOR",
    "COORDINADOR",
    "NEXO",
    "ADMIN",
    "FINANZAS",
    name="rol_asignacion",
    create_type=False,
)


def upgrade() -> None:
    postgresql.ENUM("Activo", "Inactivo", name="usuario_estado").create(
        op.get_bind(), checkfirst=True
    )
    postgresql.ENUM(
        "ALUMNO", "TUTOR", "PROFESOR", "COORDINADOR", "NEXO", "ADMIN", "FINANZAS",
        name="rol_asignacion",
    ).create(op.get_bind(), checkfirst=True)

    # --- ALTER TABLE usuarios ---
    op.add_column("usuarios", sa.Column("nombre", sa.String(100), nullable=True))
    op.add_column("usuarios", sa.Column("apellidos", sa.String(150), nullable=True))
    op.add_column("usuarios", sa.Column("dni", sa.String(512), nullable=True))
    op.add_column("usuarios", sa.Column("cuil", sa.String(512), nullable=True))
    op.add_column("usuarios", sa.Column("cbu", sa.String(512), nullable=True))
    op.add_column("usuarios", sa.Column("alias_cbu", sa.String(512), nullable=True))
    op.add_column("usuarios", sa.Column("banco", sa.String(100), nullable=True))
    op.add_column("usuarios", sa.Column("regional", sa.String(100), nullable=True))
    op.add_column("usuarios", sa.Column("legajo", sa.String(50), nullable=True))
    op.add_column(
        "usuarios", sa.Column("legajo_profesional", sa.String(50), nullable=True)
    )
    op.add_column(
        "usuarios",
        sa.Column("facturador", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "usuarios",
        sa.Column(
            "estado",
            usuario_estado,
            nullable=False,
            server_default="Activo",
        ),
    )

    # --- CREATE TABLE asignaciones ---
    op.create_table(
        "asignaciones",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("rol", rol_asignacion, nullable=False),
        sa.Column("materia_id", sa.Uuid(), nullable=True),
        sa.Column("carrera_id", sa.Uuid(), nullable=True),
        sa.Column("cohorte_id", sa.Uuid(), nullable=True),
        sa.Column("comisiones", postgresql.JSONB(), nullable=True),
        sa.Column("responsable_id", sa.Uuid(), nullable=True),
        sa.Column("desde", sa.Date(), nullable=False),
        sa.Column("hasta", sa.Date(), nullable=True),
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
        sa.ForeignKeyConstraint(["materia_id"], ["materias.id"]),
        sa.ForeignKeyConstraint(["carrera_id"], ["carreras.id"]),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohortes.id"]),
        sa.ForeignKeyConstraint(["responsable_id"], ["usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_asignaciones_tenant_id", "asignaciones", ["tenant_id"])
    op.create_index("ix_asignaciones_usuario_id", "asignaciones", ["usuario_id"])
    op.create_index("ix_asignaciones_materia_id", "asignaciones", ["materia_id"])
    op.create_index("ix_asignaciones_carrera_id", "asignaciones", ["carrera_id"])
    op.create_index("ix_asignaciones_cohorte_id", "asignaciones", ["cohorte_id"])


def downgrade() -> None:
    op.drop_index("ix_asignaciones_cohorte_id", table_name="asignaciones")
    op.drop_index("ix_asignaciones_carrera_id", table_name="asignaciones")
    op.drop_index("ix_asignaciones_materia_id", table_name="asignaciones")
    op.drop_index("ix_asignaciones_usuario_id", table_name="asignaciones")
    op.drop_index("ix_asignaciones_tenant_id", table_name="asignaciones")
    op.drop_table("asignaciones")

    op.drop_column("usuarios", "estado")
    op.drop_column("usuarios", "facturador")
    op.drop_column("usuarios", "legajo_profesional")
    op.drop_column("usuarios", "legajo")
    op.drop_column("usuarios", "regional")
    op.drop_column("usuarios", "banco")
    op.drop_column("usuarios", "alias_cbu")
    op.drop_column("usuarios", "cbu")
    op.drop_column("usuarios", "cuil")
    op.drop_column("usuarios", "dni")
    op.drop_column("usuarios", "apellidos")
    op.drop_column("usuarios", "nombre")

    postgresql.ENUM(name="rol_asignacion").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="usuario_estado").drop(op.get_bind(), checkfirst=True)
