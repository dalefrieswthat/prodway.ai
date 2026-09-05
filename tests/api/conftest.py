"""Prodway API test fixtures.

Adds apps/api to sys.path so the `app` package imports directly.
Model tests run against in-memory SQLite (model types are cross-dialect);
migrations themselves are Postgres-only and exercised outside pytest.
"""
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_api_dir = Path(__file__).resolve().parent.parent.parent / "apps" / "api"
if str(_api_dir) not in sys.path:
    sys.path.insert(0, str(_api_dir))

from app.models import Base  # noqa: E402


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, expire_on_commit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
