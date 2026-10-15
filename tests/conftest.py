"""Pytest fixture for tests that need a fresh local catalog."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from shopping_data.database import connect, initialize
from shopping_data.seed_catalog import seed_catalog


@pytest.fixture
def seeded_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> sqlite3.Connection:
    """Create a temporary database with the fictional catalog and close it after the test."""
    path = tmp_path / "shopping.db"
    monkeypatch.setenv("SHOPPING_DB_PATH", str(path))
    connection = connect(path)
    initialize(connection)
    seed_catalog(connection)
    yield connection
    connection.close()
