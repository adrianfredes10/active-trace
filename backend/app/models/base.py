"""Mixins base del modelo de datos (convenciones de `knowledge-base/04`).

- `TimestampSoftDeleteMixin`: lo hereda TODA entidad (incluido `Tenant`).
- `TenantScopedMixin`: agrega `tenant_id`; lo hereda toda entidad de dominio
  EXCEPTO `Tenant`, que es la raíz del aislamiento y no lleva `tenant_id`.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampSoftDeleteMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )


class TenantScopedMixin(TimestampSoftDeleteMixin):
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )
