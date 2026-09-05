"""Users, organizations, membership, and auth token storage."""
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampType, UuidType, new_uuid, utcnow


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UuidType, primary_key=True, default=new_uuid)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(TimestampType, default=utcnow)

    memberships: Mapped[list["OrganizationMember"]] = relationship(back_populates="user")


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(UuidType, primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(200))
    # Set only through the explicit Slack workspace linking flow (never inferred).
    slack_team_id: Mapped[str | None] = mapped_column(String(20), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(TimestampType, default=utcnow)

    members: Mapped[list["OrganizationMember"]] = relationship(back_populates="organization")


class OrganizationMember(Base):
    __tablename__ = "organization_members"
    __table_args__ = (UniqueConstraint("user_id", "organization_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UuidType, primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id"), index=True
    )
    role: Mapped[str] = mapped_column(String(20), default="owner")
    created_at: Mapped[datetime] = mapped_column(TimestampType, default=utcnow)

    user: Mapped[User] = relationship(back_populates="memberships")
    organization: Mapped[Organization] = relationship(back_populates="members")


class Session(Base):
    """Server-side web session; the cookie stores only the opaque token."""

    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(UuidType, primary_key=True, default=new_uuid)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    expires_at: Mapped[datetime] = mapped_column(TimestampType)
    created_at: Mapped[datetime] = mapped_column(TimestampType, default=utcnow)


class MagicLinkToken(Base):
    __tablename__ = "magic_link_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UuidType, primary_key=True, default=new_uuid)
    email: Mapped[str] = mapped_column(String(320), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(TimestampType)
    used_at: Mapped[datetime | None] = mapped_column(TimestampType)
    created_at: Mapped[datetime] = mapped_column(TimestampType, default=utcnow)
