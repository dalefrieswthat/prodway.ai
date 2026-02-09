"""Cursor context folder watcher and ingestor.

This ingestor watches cursor-context folders across multiple projects
and ingests any changes to the context engine.
"""

import asyncio
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Callable

import structlog
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from src.core.config import get_settings
from src.core.models import Source

logger = structlog.get_logger()
settings = get_settings()


class CursorContextHandler(FileSystemEventHandler):
    """Handler for file system events in cursor-context folders."""

    def __init__(self, callback: Callable[[Path, str], None]):
        self.callback = callback
        self._processed_hashes: set[str] = set()

    def _get_file_hash(self, path: Path) -> str:
        """Get hash of file content to detect actual changes."""
        try:
            content = path.read_text()
            return hashlib.md5(content.encode()).hexdigest()
        except Exception:
            return ""

    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return

        path = Path(event.src_path)
        if not self._should_process(path):
            return

        file_hash = self._get_file_hash(path)
        if file_hash in self._processed_hashes:
            return

        self._processed_hashes.add(file_hash)
        logger.info("Context file modified", path=str(path))

        try:
            content = path.read_text()
            self.callback(path, content)
        except Exception as e:
            logger.error("Failed to process context file", path=str(path), error=str(e))

    def on_created(self, event: FileSystemEvent) -> None:
        self.on_modified(event)

    def _should_process(self, path: Path) -> bool:
        """Check if file should be processed."""
        # Only process markdown, text, and common context files
        valid_extensions = {".md", ".txt", ".json", ".yaml", ".yml"}
        if path.suffix.lower() not in valid_extensions:
            return False

        # Skip hidden files
        if path.name.startswith("."):
            return False

        return True


class CursorContextIngestor:
    """Ingestor for cursor-context folders across projects."""

    def __init__(self):
        self.observers: list[Observer] = []
        self.context_paths = settings.context_paths

    async def start(self, on_content: Callable[[Path, str, Source], None]) -> None:
        """Start watching all configured context paths."""

        def callback(path: Path, content: str) -> None:
            on_content(path, content, Source.CURSOR)

        for context_path in self.context_paths:
            if not context_path.exists():
                logger.warning("Context path does not exist", path=str(context_path))
                continue

            logger.info("Starting watcher", path=str(context_path))

            handler = CursorContextHandler(callback)
            observer = Observer()
            observer.schedule(handler, str(context_path), recursive=True)
            observer.start()
            self.observers.append(observer)

            # Initial scan
            await self._scan_existing(context_path, callback)

        logger.info("Context watchers started", count=len(self.observers))

    async def _scan_existing(
        self,
        path: Path,
        callback: Callable[[Path, str], None]
    ) -> None:
        """Scan existing files in a context folder."""
        for file_path in path.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith("."):
                try:
                    content = file_path.read_text()
                    callback(file_path, content)
                except Exception as e:
                    logger.error("Failed to scan file", path=str(file_path), error=str(e))

    def stop(self) -> None:
        """Stop all observers."""
        for observer in self.observers:
            observer.stop()
            observer.join()
        self.observers.clear()
        logger.info("Context watchers stopped")


async def main():
    """Test the cursor context ingestor."""

    def on_content(path: Path, content: str, source: Source) -> None:
        print(f"[{source}] {path.name}: {len(content)} chars")

    ingestor = CursorContextIngestor()
    await ingestor.start(on_content)

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        ingestor.stop()


if __name__ == "__main__":
    asyncio.run(main())
