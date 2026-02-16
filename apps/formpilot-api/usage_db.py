"""
Minimal usage stats DB: forms_filled, sows_sent. SQLite by default; set DATABASE_URL for Postgres.
"""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

# Default: SQLite file next to the app (e.g. in Railway ephemeral disk or local)
DATA_DIR = Path(__file__).resolve().parent
SQLITE_PATH = DATA_DIR / "prodway_usage.db"

_conn: sqlite3.Connection | None = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(str(SQLITE_PATH), check_same_thread=False)
        _conn.execute("""
            CREATE TABLE IF NOT EXISTS usage_stats (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                forms_filled INTEGER NOT NULL DEFAULT 0,
                sows_sent INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        _conn.execute(
            "INSERT OR IGNORE INTO usage_stats (id, forms_filled, sows_sent) VALUES (1, 0, 0)"
        )
        _conn.commit()
    return _conn


@contextmanager
def _cursor():
    conn = _get_conn()
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    finally:
        cur.close()


def get_stats() -> tuple[int, int]:
    """Return (forms_filled, sows_sent)."""
    with _cursor() as cur:
        cur.execute(
            "SELECT forms_filled, sows_sent FROM usage_stats WHERE id = 1"
        )
        row = cur.fetchone()
        return (row[0], row[1]) if row else (0, 0)


def record_forms_filled(delta: int = 1) -> None:
    if delta <= 0:
        return
    with _cursor() as cur:
        cur.execute(
            "UPDATE usage_stats SET forms_filled = forms_filled + ?, updated_at = datetime('now') WHERE id = 1",
            (delta,),
        )


def record_sows_sent(delta: int = 1) -> None:
    if delta <= 0:
        return
    with _cursor() as cur:
        cur.execute(
            "UPDATE usage_stats SET sows_sent = sows_sent + ?, updated_at = datetime('now') WHERE id = 1",
            (delta,),
        )
