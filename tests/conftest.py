"""Shared test fixtures for Prodway test suite."""
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def env_defaults(monkeypatch):
    """Set minimal env vars so app modules can be imported without real credentials."""
    defaults = {
        "SLACK_CLIENT_ID": "test-client-id",
        "SLACK_CLIENT_SECRET": "test-client-secret",
        "SLACK_SIGNING_SECRET": "test-signing-secret",
        "ANTHROPIC_API_KEY": "",
        "GOOGLE_API_KEY": "test-google-key",
        "DEFAULT_AI_PROVIDER": "gemini",
        "STRIPE_SECRET_KEY": "",
        "STRIPE_CLIENT_ID": "",
        "STRIPE_WEBHOOK_SECRET": "",
        "STRIPE_PRICE_BASE_ID": "price_test_base",
        "STRIPE_PRICE_USAGE_ID": "price_test_usage",
        "DOCUSIGN_INTEGRATION_KEY": "",
        "DOCUSIGN_SECRET_KEY": "",
        "ENCRYPTION_KEY": "",
        "SENDGRID_API_KEY": "",
        "APP_URL": "https://api.prodway.ai",
        "SOWFLOW_API_URL": "http://localhost:3000",
    }
    for k, v in defaults.items():
        monkeypatch.setenv(k, v)


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Create a temporary data directory matching SowFlow's layout."""
    for subdir in ["installations", "states", "sows", "integrations",
                    "api_tokens", "invoices", "audit", "edits",
                    "generations", "outcomes"]:
        (tmp_path / subdir).mkdir()
    return tmp_path


@pytest.fixture
def sample_sow():
    """A realistic SOW dict as produced by AI generation."""
    return {
        "title": "Kubernetes Migration",
        "executive_summary": "Migrate monolith to K8s cluster with HA and auto-scaling.",
        "scope": [
            "Container packaging for 3 services",
            "Helm chart development",
            "CI/CD pipeline integration",
            "Monitoring and alerting setup",
        ],
        "deliverables": [
            "Dockerfiles for all services",
            "Helm charts with values per environment",
            "GitHub Actions workflow",
            "Runbook documentation",
        ],
        "timeline": [
            {"phase": "Phase 1: Assessment", "duration": "1 week", "description": "Audit existing infra"},
            {"phase": "Phase 2: Migration", "duration": "3 weeks", "description": "Containerize and deploy"},
            {"phase": "Phase 3: Hardening", "duration": "1 week", "description": "Monitoring and load testing"},
        ],
        "pricing": {
            "total": 35000,
            "currency": "USD",
            "structure": "50% upfront, 50% on completion",
            "payment_schedule": [
                {"milestone": "Signed Agreement", "amount": 17500, "due": "Upon signing"},
                {"milestone": "Project Completion", "amount": 17500, "due": "On delivery"},
            ],
        },
        "assumptions": ["Client provides AWS access", "Existing CI pipeline"],
        "exclusions": ["Ongoing maintenance", "Performance optimization beyond initial targets"],
    }


@pytest.fixture
def sample_profile():
    """A realistic company profile for FormPilot tests."""
    return {
        "companyName": "Prodway AI",
        "contactName": "Dale Yarborough",
        "email": "dale@prodway.ai",
        "phone": "+1-512-555-0199",
        "website": "https://prodway.ai",
        "linkedinUrl": "https://linkedin.com/company/prodway",
        "city": "Austin",
        "state": "TX",
        "country": "US",
        "zip": "78701",
        "description": "AI tools for service businesses to scale without scaling headcount.",
    }


@pytest.fixture
def sample_form_fields():
    """Realistic form fields as detected by the Chrome extension."""
    return [
        {"selector": "#company", "label": "Company Name", "name": "company", "semanticType": "companyName", "value": ""},
        {"selector": "#email", "label": "Email", "name": "email", "semanticType": "email", "value": ""},
        {"selector": "#phone", "label": "Phone", "name": "phone", "semanticType": "phone", "value": ""},
        {"selector": "#website", "label": "Website", "name": "website", "semanticType": "website", "value": ""},
        {"selector": "#linkedin", "label": "LinkedIn URL", "name": "linkedin", "semanticType": "linkedinUrl", "value": ""},
        {"selector": "#description", "label": "Describe your company", "name": "desc", "semanticType": "shortDescription", "value": ""},
        {"selector": "#firstName", "label": "First Name", "name": "first_name", "semanticType": "firstName", "value": ""},
        {"selector": "#lastName", "label": "Last Name", "name": "last_name", "semanticType": "lastName", "value": ""},
    ]
