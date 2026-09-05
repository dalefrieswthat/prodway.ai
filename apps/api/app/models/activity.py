"""Append-only activity events: foundational engagement history."""
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, JsonType, TimestampType, UuidType, new_uuid, utcnow


class ActivityEvent(Base):
    __tablename__ = "activity_events"

    id: Mapped[uuid.UUID] = mapped_column(UuidType, primary_key=True, default=new_uuid)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id"), index=True
    )
    engagement_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("engagements.id"), index=True
    )
    # e.g. engagement.created, sow.generated, sow.updated, sow.version_frozen
    type: Mapped[str] = mapped_column(String(50), index=True)
    payload: Mapped[dict | None] = mapped_column(JsonType)
    created_at: Mapped[datetime] = mapped_column(TimestampType, default=utcnow, index=True)
