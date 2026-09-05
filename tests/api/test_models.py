"""Model round-trip tests proving the Phase 1 schema."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.models import (
    ActivityEvent,
    Client,
    Engagement,
    EngagementStatus,
    Organization,
    OrganizationMember,
    Sow,
    SowVersion,
    User,
)


def _seed_org_and_user(db):
    org = Organization(name="Dale Consulting")
    user = User(email="dale@prodway.ai", name="Dale")
    db.add_all([org, user])
    db.flush()
    db.add(OrganizationMember(user_id=user.id, organization_id=org.id, role="owner"))
    db.commit()
    return org, user


def test_full_engagement_graph_round_trip(db_session):
    org, user = _seed_org_and_user(db_session)

    client = Client(
        organization_id=org.id,
        name="Acme",
        company="Acme Corp",
        contact_email="ops@acme.com",
    )
    db_session.add(client)
    db_session.flush()

    engagement = Engagement(
        organization_id=org.id,
        client_id=client.id,
        name="AWS Infrastructure Migration",
        description="Two-week infra engagement",
        total_value=Decimal("30000.00"),
        payment_model="deposit_completion",
        payment_schedule=[
            {"label": "Deposit", "amount": 15000, "due": "on_signing"},
            {"label": "Completion", "amount": 15000, "due": "on_completion"},
        ],
    )
    db_session.add(engagement)
    db_session.flush()

    sow = Sow(engagement_id=engagement.id)
    db_session.add(sow)
    db_session.flush()

    version = SowVersion(
        sow_id=sow.id,
        version_number=1,
        content={
            "overview": "This Statement of Work covers...",
            "deliverables": ["EKS deployment", "CI/CD pipeline"],
            "acceptance_criteria": ["All services pass health checks"],
            "exclusions": ["Application feature development"],
        },
        frozen_reason="generated",
    )
    db_session.add(version)
    db_session.flush()
    sow.current_version_id = version.id

    db_session.add(
        ActivityEvent(
            organization_id=org.id,
            engagement_id=engagement.id,
            type="engagement.created",
            payload={"source": "test"},
        )
    )
    db_session.commit()

    loaded = db_session.get(Engagement, engagement.id)
    assert loaded.status == EngagementStatus.draft
    assert loaded.total_value == Decimal("30000.00")
    assert loaded.payment_schedule[0]["label"] == "Deposit"

    loaded_sow = db_session.get(Sow, sow.id)
    assert loaded_sow.current_version_id == version.id
    assert loaded_sow.versions[0].content["deliverables"] == [
        "EKS deployment",
        "CI/CD pipeline",
    ]
    assert loaded_sow.versions[0].frozen_reason == "generated"

    events = db_session.query(ActivityEvent).filter_by(engagement_id=engagement.id).all()
    assert [e.type for e in events] == ["engagement.created"]


def test_engagement_status_defaults_and_transitions(db_session):
    org, _ = _seed_org_and_user(db_session)
    client = Client(organization_id=org.id, name="NexWorks")
    db_session.add(client)
    db_session.flush()

    e = Engagement(organization_id=org.id, client_id=client.id, name="AI Platform")
    db_session.add(e)
    db_session.commit()

    assert e.status == EngagementStatus.draft
    assert e.currency == "USD"

    e.status = EngagementStatus.sow_ready
    db_session.commit()
    assert db_session.get(Engagement, e.id).status == EngagementStatus.sow_ready


def test_sow_version_numbers_unique_per_sow(db_session):
    org, _ = _seed_org_and_user(db_session)
    client = Client(organization_id=org.id, name="OurFirm")
    db_session.add(client)
    db_session.flush()
    e = Engagement(organization_id=org.id, client_id=client.id, name="Infra")
    db_session.add(e)
    db_session.flush()
    sow = Sow(engagement_id=e.id)
    db_session.add(sow)
    db_session.flush()

    db_session.add(SowVersion(sow_id=sow.id, version_number=1, content={}))
    db_session.commit()

    import pytest
    from sqlalchemy.exc import IntegrityError

    db_session.add(SowVersion(sow_id=sow.id, version_number=1, content={}))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_user_email_unique(db_session):
    import pytest
    from sqlalchemy.exc import IntegrityError

    db_session.add(User(email="dale@prodway.ai"))
    db_session.commit()
    db_session.add(User(email="dale@prodway.ai"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
