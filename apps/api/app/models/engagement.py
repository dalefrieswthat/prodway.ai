"""Engagement: the product core.

The status enum is intentionally small. Signature state and payment state
become separate tables/dimensions in later phases; composite display statuses
are computed in the API, never stored here.
"""
import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, JsonType, TimestampType, UuidType, new_uuid, utcnow


class EngagementStatus(str, enum.Enum):
    draft = "draft"
    sow_ready = "sow_ready"
    active = "active"
    completed = "completed"
    cancelled = "cancelled"


class Engagement(Base):
    __tablename__ = "engagements"

    id: Mapped[uuid.UUID] = mapped_column(UuidType, primary_key=True, default=new_uuid)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id"), index=True
    )
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id"), index=True)
    name: Mapped[str] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[EngagementStatus] = mapped_column(
        Enum(EngagementStatus, name="engagement_status", native_enum=False, length=20),
        default=EngagementStatus.draft,
        index=True,
    )
    total_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    # fixed_fee | deposit_completion | milestones | hourly | retainer | custom
    payment_model: Mapped[str | None] = mapped_column(String(30))
    # Structured schedule entries: [{"label", "amount", "due"}]
    payment_schedule: Mapped[list | None] = mapped_column(JsonType)
    start_date: Mapped[date | None] = mapped_column(Date)
    target_end_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(TimestampType, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        TimestampType, default=utcnow, onupdate=utcnow
    )

    sow: Mapped["Sow | None"] = relationship(back_populates="engagement")  # noqa: F821
