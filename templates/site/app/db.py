"""SQLite: one short-lived connection per request, WAL mode, and additive migrations that run on every connect."""
from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

from .config import DB_PATH

SCHEMA = '''
CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    csrf_token TEXT NOT NULL,
    email TEXT NOT NULL,
    expires_at INTEGER NOT NULL,
    created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at INTEGER NOT NULL
);
'''

# Add new columns here instead of editing SCHEMA: existing databases get them on the next connect.
# { table: { column: 'SQL type and default' } }
ADDITIONS: dict[str, dict[str, str]] = {}


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.parent.chmod(0o700)
    db = sqlite3.connect(path, timeout=5)
    path.chmod(0o600)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA busy_timeout=5000')
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA foreign_keys=ON')
    with db:
        db.executescript(SCHEMA)
        for table, columns in ADDITIONS.items():
            have = {r['name'] for r in db.execute(f'PRAGMA table_info({table})')}
            for name, definition in columns.items():
                if name not in have:
                    db.execute(f'ALTER TABLE {table} ADD COLUMN {name} {definition}')
    return db


def get_db() -> Iterator[sqlite3.Connection]:
    """FastAPI dependency: `db: sqlite3.Connection = Depends(get_db)`."""
    db = connect()
    try:
        yield db
    finally:
        db.close()
