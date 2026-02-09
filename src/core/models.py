"""Shared data models."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Source(StrEnum):
    """Data source types."""

    SLACK = "slack"
    GITHUB = "github"
    GMAIL = "gmail"
    NOTION = "notion"
    LINKEDIN = "linkedin"
    CURSOR = "cursor"


class MessageType(StrEnum):
    """Message/content types."""

    CHAT = "chat"
    EMAIL = "email"
    COMMIT = "commit"
    PR_REVIEW = "pr_review"
    DOCUMENT = "document"
    CODE = "code"
    UPDATE = "update"


class PatternType(StrEnum):
    """Learned pattern types."""

    COMMUNICATION = "communication"
    CODE_STYLE = "code_style"
    DECISION = "decision"
    TEMPLATE = "template"


# --- Request/Response Models ---


class IngestRequest(BaseModel):
    """Request to ingest content from a source."""

    source: Source
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DraftRequest(BaseModel):
    """Request to generate a draft response."""

    context: str  # The message/situation to respond to
    draft_type: MessageType
    source: Source  # Where will this be sent
    additional_context: str | None = None
    tone: str | None = None  # Optional tone override


class DraftResponse(BaseModel):
    """Generated draft response."""

    draft_id: str
    content: str
    confidence: float  # 0-1, how confident the AI is
    sources_used: list[str]  # IDs of context sources used
    requires_approval: bool = True


class ApprovalRequest(BaseModel):
    """Request to approve/reject a draft."""

    draft_id: str
    approved: bool
    edits: str | None = None  # Optional edits before sending
    feedback: str | None = None  # Feedback for learning


class ContextSearchRequest(BaseModel):
    """Request to search context."""

    query: str
    sources: list[Source] | None = None
    limit: int = Field(default=10, le=50)
    include_embeddings: bool = False


class ContextSearchResult(BaseModel):
    """A single context search result."""

    id: str
    content: str
    source: Source
    score: float  # Similarity score
    metadata: dict[str, Any]
    timestamp: datetime


class ContextSearchResponse(BaseModel):
    """Response from context search."""

    results: list[ContextSearchResult]
    query_embedding_id: str | None = None
    total_searched: int
