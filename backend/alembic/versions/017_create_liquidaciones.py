"""create liquidaciones tables

Revision ID: 017
Revises: 016
Create Date: 2026-06-16

C-18: salarios_base, salarios_plus, liquidaciones, facturas; plus_grupo en materias.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "017"
down_revision: str | None = "016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_rol = postgresql.ENUM(
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
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE liquidacion_estado AS ENUM ('Abierta', 'Cerrada');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE factura_estado AS ENUM ('Pendiente', 'Abonada');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
        """
    )

    liquidacion_estado = postgresql.ENUM(
        "Abierta", "Cerrada", name="liquidacion_estado", create_type=False
    )
    factura_estado = postgresql.ENUM(
        "Pendiente", "Abonada", name="factura_estado", create_type=False
    )

    op.add_column("materias", sa.Column("plus_grupo", sa.String(50), nullable=True))

    op.create_table(
        "salarios_base",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rol", _rol, nullable=False),
        sa.Column("monto", sa.Numeric(14, 2), nullable=False),
        sa.Column("vig_desde", sa.Date(), nullable=False),
        sa.Column("vig_hasta", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
    )
    op.create_index("ix_salarios_base_tenant_id", "salarios_base", ["tenant_id"])

    op.create_table(
        "salarios_plus",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("grupo", sa.String(50), nullable=False),
        sa.Column("rol", _rol, nullable=False),
        sa.Column("descripcion", sa.String(255), nullable=True),
        sa.Column("monto", sa.Numeric(14, 2), nullable=False),
        sa.Column("vig_desde", sa.Date(), nullable=False),
        sa.Column("vig_hasta", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
    )
    op.create_index("ix_salarios_plus_tenant_id", "salarios_plus", ["tenant_id"])
    op.create_index("ix_salarios_plus_grupo", "salarios_plus", ["grupo"])

    op.create_table(
        "liquidaciones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cohorte_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("periodo", sa.String(7), nullable=False),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rol", _rol, nullable=False),
        sa.Column("comisiones", postgresql.JSONB(), nullable=False),
        sa.Column("monto_base", sa.Numeric(14, 2), nullable=False),
        sa.Column("monto_plus", sa.Numeric(14, 2), nullable=False),
        sa.Column("total", sa.Numeric(14, 2), nullable=False),
        sa.Column("es_nexo", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "excluido_por_factura", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("estado", liquidacion_estado, nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohortes.id"]),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
        sa.UniqueConstraint(
            "tenant_id",
            "cohorte_id",
            "periodo",
            "usuario_id",
            "rol",
            name="uq_liquidaciones_tenant_cohorte_periodo_usuario_rol",
        ),
    )
    op.create_index("ix_liquidaciones_tenant_id", "liquidaciones", ["tenant_id"])
    op.create_index("ix_liquidaciones_periodo", "liquidaciones", ["periodo"])
    op.create_index("ix_liquidaciones_cohorte_id", "liquidaciones", ["cohorte_id"])
    op.create_index("ix_liquidaciones_usuario_id", "liquidaciones", ["usuario_id"])

    op.create_table(
        "facturas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("periodo", sa.String(7), nullable=False),
        sa.Column("detalle", sa.Text(), nullable=False),
        sa.Column("referencia_archivo", sa.String(512), nullable=True),
        sa.Column("tamano_kb", sa.Numeric(10, 2), nullable=True),
        sa.Column("estado", factura_estado, nullable=False),
        sa.Column("cargada_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("abonada_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
    )
    op.create_index("ix_facturas_tenant_id", "facturas", ["tenant_id"])
    op.create_index("ix_facturas_usuario_id", "facturas", ["usuario_id"])
    op.create_index("ix_facturas_periodo", "facturas", ["periodo"])


def downgrade() -> None:
    op.drop_table("facturas")
    op.drop_table("liquidaciones")
    op.drop_table("salarios_plus")
    op.drop_table("salarios_base")
    op.drop_column("materias", "plus_grupo")
    op.execute("DROP TYPE IF EXISTS factura_estado")
    op.execute("DROP TYPE IF EXISTS liquidacion_estado")
