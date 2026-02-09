"""FastAPI application entry point."""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting Context Engine", env=settings.app_env)
    
    # Startup: Initialize connections
    # TODO: Initialize database pool
    # TODO: Initialize Pinecone client
    # TODO: Initialize Redis connection
    
    yield
    
    # Shutdown: Clean up
    logger.info("Shutting down Context Engine")


app = FastAPI(
    title="Context Engine",
    description="AI-powered context aggregation and agent platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not settings.is_production else ["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "env": settings.app_env}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Context Engine",
        "version": "0.1.0",
        "docs": "/docs",
    }


# --- Routes will be added here ---

# from src.api.routes import ingest, agents, context
# app.include_router(ingest.router, prefix="/api/v1/ingest", tags=["ingest"])
# app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
# app.include_router(context.router, prefix="/api/v1/context", tags=["context"])
