"""SOW and versions.

Canonical SOW content is structured data (JSON sections), never an HTML or
rich-text blob. Documents (PDF, DocuSign envelope) are renderings of a frozen
version.
"""
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, JsonType, TimestampType, UuidType, new_uuid, utcnow


class Sow(Base):
    __tablename__ = "sows"

    id: Mapped[uuid.UUID] = mapped_column(UuidType, primary_key=True, default=new_uuid)
    engagement_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("engagements.id"), unique=True, index=True
    )
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("sow_versions.id", use_alter=True, name="fk_sows_current_version")
    )
    created_at: Mapped[datetime] = mapped_column(TimestampType, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        TimestampType, default=utcnow, onupdate=utcnow
    )

    engagement: Mapped["Engagement"] = relationship(back_populates="sow")  # noqa: F821
    versions: Mapped[list["SowVersion"]] = relationship(
        back_populates="sow",
        foreign_keys="SowVersion.sow_id",
        order_by="SowVersion.version_number",
    )


class SowVersion(Base):
    """A frozen or working snapshot of structured SOW content.

    content sections: overview, objectives, scope, deliverables[],
    acceptance_criteria[], assumptions[], client_responsibilities[],
    exclusions[], timeline, commercial_terms, change_control, legal_terms.
    """

    __tablename__ = "sow_versions"
    __table_args__ = (UniqueConstraint("sow_id", "version_number"),)

    id: Mapped[uuid.UUID] = mapped_column(UuidType, primary_key=True, default=new_uuid)
    sow_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sows.id"), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    content: Mapped[dict] = mapped_column(JsonType)
    # generated | manual | exported | sent | signed (null = working copy)
    frozen_reason: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(TimestampType, default=utcnow)

    sow: Mapped[Sow] = relationship(back_populates="versions", foreign_keys=[sow_id])
