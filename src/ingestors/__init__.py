"""Data ingestors for various platforms."""

from src.ingestors.cursor_context import CursorContextIngestor
from src.ingestors.slack import SlackIngestor
from src.ingestors.github import GitHubIngestor

__all__ = ["CursorContextIngestor", "SlackIngestor", "GitHubIngestor"]
