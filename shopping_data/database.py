"""SQLite setup and transaction helpers for the local shopping catalog."""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / "shopping.db"
SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def database_path() -> Path:
    """Return the configured database path, resolving relative paths at the project root."""
    configured = os.environ.get("SHOPPING_DB_PATH", "shopping.db")
    path = Path(configured).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def connect(path: str | Path | None = None) -> sqlite3.Connection:
    """Open a SQLite connection with foreign keys and safe row access enabled."""
    db_path = Path(path) if path is not None else database_path()
    if str(db_path) != ":memory:":
        db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(db_path), timeout=10, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


def initialize(connection: sqlite3.Connection) -> None:
    """Create the schema from the adjacent SQL file."""
    connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))


@contextmanager
def open_database(path: str | Path | None = None) -> Iterator[sqlite3.Connection]:
    """Open and reliably close a database connection."""
    connection = connect(path)
    try:
        yield connection
    finally:
        connection.close()


@contextmanager
def write_transaction(connection: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Serialize a local write operation and roll it back on every failure."""
    connection.execute("BEGIN IMMEDIATE")
    try:
        yield connection
    except BaseException:
        connection.rollback()
        raise
    else:
        connection.commit()
