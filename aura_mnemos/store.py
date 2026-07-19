"""Mnemos shared store: db path resolution, connection, schema init."""

import os
import sqlite3
from pathlib import Path

DB_ENV = "MNEMOS_DB"
DEFAULT_DB = "~/.mnemos/mnemos.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    content    TEXT NOT NULL,
    tags       TEXT,
    source     TEXT,
    created_at TEXT NOT NULL
);
"""


def resolve_db_path() -> Path:
    """MNEMOS_DB env if set, else ~/.mnemos/mnemos.db (expanded)."""
    raw = os.environ.get(DB_ENV)
    if raw:
        return Path(raw).expanduser().resolve()
    return Path(DEFAULT_DB).expanduser().resolve()


def connect(db_path=None) -> sqlite3.Connection:
    """Open sqlite3 connection with Row factory."""
    path = Path(db_path) if db_path is not None else resolve_db_path()
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path=None) -> None:
    """Create parent dir if missing and ensure the memories table exists."""
    path = Path(db_path) if db_path is not None else resolve_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
