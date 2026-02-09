"""Slack data ingestor.

Handles:
- Slack export ingestion (JSON files from workspace export)
- Real-time message ingestion via Slack API
- Pattern extraction from messages
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from src.core.config import get_settings
from src.core.models import MessageType, Source

logger = structlog.get_logger()
settings = get_settings()


class SlackIngestor:
    """Ingestor for Slack messages and exports."""

    def __init__(self):
        self.client = WebClient(token=settings.slack_bot_token) if settings.slack_bot_token else None

    async def ingest_export(self, export_path: Path) -> list[dict[str, Any]]:
        """
        Ingest a Slack workspace export.

        Export structure:
        export/
        ├── channels.json
        ├── users.json
        └── channel-name/
            ├── 2024-01-01.json
            └── 2024-01-02.json
        """
        messages = []

        if not export_path.exists():
            logger.error("Export path does not exist", path=str(export_path))
            return messages

        # Load users for name resolution
        users_file = export_path / "users.json"
        users = {}
        if users_file.exists():
            with open(users_file) as f:
                users_data = json.load(f)
                users = {u["id"]: u.get("real_name", u.get("name", "Unknown")) for u in users_data}

        # Process each channel directory
        for channel_dir in export_path.iterdir():
            if not channel_dir.is_dir():
                continue

            channel_name = channel_dir.name

            # Process each day's messages
            for msg_file in channel_dir.glob("*.json"):
                try:
                    with open(msg_file) as f:
                        day_messages = json.load(f)

                    for msg in day_messages:
                        if msg.get("subtype") in ["channel_join", "channel_leave", "bot_message"]:
                            continue

                        processed = self._process_message(msg, channel_name, users)
                        if processed:
                            messages.append(processed)

                except Exception as e:
                    logger.error("Failed to process message file", file=str(msg_file), error=str(e))

        logger.info("Ingested Slack export", message_count=len(messages))
        return messages

    def _process_message(
        self,
        msg: dict[str, Any],
        channel: str,
        users: dict[str, str]
    ) -> dict[str, Any] | None:
        """Process a single Slack message."""
        text = msg.get("text", "")
        if not text or len(text) < 10:  # Skip very short messages
            return None

        user_id = msg.get("user", "")
        timestamp = msg.get("ts", "")

        return {
            "source": Source.SLACK,
            "message_type": MessageType.CHAT,
            "content": text,
            "author": users.get(user_id, user_id),
            "author_id": user_id,
            "channel": channel,
            "timestamp": datetime.fromtimestamp(float(timestamp)) if timestamp else datetime.utcnow(),
            "metadata": {
                "reactions": msg.get("reactions", []),
                "thread_ts": msg.get("thread_ts"),
                "reply_count": msg.get("reply_count", 0),
            },
        }

    async def fetch_recent_messages(
        self,
        channel_id: str,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """Fetch recent messages from a channel via API."""
        if not self.client:
            logger.error("Slack client not configured")
            return []

        try:
            result = self.client.conversations_history(
                channel=channel_id,
                limit=limit,
            )

            messages = []
            for msg in result.get("messages", []):
                processed = self._process_message(msg, channel_id, {})
                if processed:
                    messages.append(processed)

            return messages

        except SlackApiError as e:
            logger.error("Slack API error", error=str(e))
            return []

    async def get_my_messages(self, user_id: str, limit: int = 500) -> list[dict[str, Any]]:
        """
        Get messages authored by a specific user.

        This is useful for learning the user's communication patterns.
        """
        if not self.client:
            logger.error("Slack client not configured")
            return []

        try:
            result = self.client.search_messages(
                query=f"from:<@{user_id}>",
                count=limit,
            )

            messages = []
            for match in result.get("messages", {}).get("matches", []):
                messages.append({
                    "source": Source.SLACK,
                    "message_type": MessageType.CHAT,
                    "content": match.get("text", ""),
                    "channel": match.get("channel", {}).get("name", "unknown"),
                    "timestamp": datetime.fromtimestamp(float(match.get("ts", 0))),
                    "metadata": {
                        "permalink": match.get("permalink"),
                    },
                })

            return messages

        except SlackApiError as e:
            logger.error("Slack API error", error=str(e))
            return []
