"""Declarative base and shared column types."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()


# JSONB on Postgres, plain JSON elsewhere (keeps tests runnable on SQLite).
JsonType = JSON().with_variant(JSONB(), "postgresql")

# Timezone-aware timestamps everywhere.
TimestampType = DateTime(timezone=True)

UuidType = Uuid()


class Base(DeclarativeBase):
    pass
