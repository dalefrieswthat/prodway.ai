"""Prodway API application factory.

All Prodway surfaces (web app, Slack, extension, future agents) operate on the
Engagement domain through this API. Domain logic lives here, never in clients.
"""
from fastapi import FastAPI

from app.routers import health


def create_app() -> FastAPI:
    app = FastAPI(
        title="Prodway API",
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
    )
    app.include_router(health.router, prefix="/v1")
    return app


app = create_app()
