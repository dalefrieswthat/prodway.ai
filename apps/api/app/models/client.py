"""Client entity: the customer of the consultant."""
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampType, UuidType, new_uuid, utcnow


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(UuidType, primary_key=True, default=new_uuid)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    company: Mapped[str | None] = mapped_column(String(200))
    contact_name: Mapped[str | None] = mapped_column(String(200))
    contact_email: Mapped[str | None] = mapped_column(String(320))
    contact_phone: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(TimestampType, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        TimestampType, default=utcnow, onupdate=utcnow
    )
