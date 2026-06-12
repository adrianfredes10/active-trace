"""create rbac tables

Revision ID: 003
Revises: 002
Create Date: 2026-06-12

Tablas RBAC (C-04): roles, permisos, roles_permisos, usuarios_roles.
Seed idempotente de la matriz base por tenant existente.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.services.rbac_seed import seed_tenant_rbac_sync

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("codigo", sa.String(length=50), nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False),
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
        sa.UniqueConstraint("tenant_id", "codigo", name="uq_roles_tenant_codigo"),
    )
    op.create_index("ix_roles_tenant_id", "roles", ["tenant_id"])
    op.create_index("ix_roles_codigo", "roles", ["codigo"])

    op.create_table(
        "permisos",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("modulo", sa.String(length=50), nullable=False),
        sa.Column("accion", sa.String(length=50), nullable=False),
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
        sa.UniqueConstraint(
            "tenant_id",
            "modulo",
            "accion",
            name="uq_permisos_tenant_modulo_accion",
        ),
    )
    op.create_index("ix_permisos_tenant_id", "permisos", ["tenant_id"])

    op.create_table(
        "roles_permisos",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("rol_id", sa.Uuid(), nullable=False),
        sa.Column("permiso_id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(["rol_id"], ["roles.id"]),
        sa.ForeignKeyConstraint(["permiso_id"], ["permisos.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "rol_id",
            "permiso_id",
            name="uq_roles_permisos_tenant_pair",
        ),
    )
    op.create_index("ix_roles_permisos_tenant_id", "roles_permisos", ["tenant_id"])
    op.create_index("ix_roles_permisos_rol_id", "roles_permisos", ["rol_id"])
    op.create_index("ix_roles_permisos_permiso_id", "roles_permisos", ["permiso_id"])

    op.create_table(
        "usuarios_roles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("rol_id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(["rol_id"], ["roles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "usuario_id",
            "rol_id",
            name="uq_usuarios_roles_tenant_pair",
        ),
    )
    op.create_index("ix_usuarios_roles_tenant_id", "usuarios_roles", ["tenant_id"])
    op.create_index("ix_usuarios_roles_usuario_id", "usuarios_roles", ["usuario_id"])
    op.create_index("ix_usuarios_roles_rol_id", "usuarios_roles", ["rol_id"])

    conn = op.get_bind()
    tenants = conn.execute(
        sa.text("SELECT id FROM tenants WHERE deleted_at IS NULL")
    ).fetchall()
    for (tenant_id,) in tenants:
        seed_tenant_rbac_sync(conn, tenant_id)


def downgrade() -> None:
    op.drop_table("usuarios_roles")
    op.drop_table("roles_permisos")
    op.drop_table("permisos")
    op.drop_table("roles")
