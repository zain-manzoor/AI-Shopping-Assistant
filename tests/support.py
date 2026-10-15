"""Shared temporary SQLite setup for standard-library and pytest runs."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from shopping_data.database import connect, initialize
from shopping_data.seed_catalog import seed_catalog


class ShoppingDatabaseTestCase(unittest.TestCase):
    """Provide a fresh seeded file database for each isolated test."""

    def setUp(self) -> None:
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.database_file = Path(self._temporary_directory.name) / "shopping.db"
        self._old_database_path = os.environ.get("SHOPPING_DB_PATH")
        os.environ["SHOPPING_DB_PATH"] = str(self.database_file)
        self.connection = connect()
        initialize(self.connection)
        seed_catalog(self.connection)

    def tearDown(self) -> None:
        self.connection.close()
        if self._old_database_path is None:
            os.environ.pop("SHOPPING_DB_PATH", None)
        else:
            os.environ["SHOPPING_DB_PATH"] = self._old_database_path
        self._temporary_directory.cleanup()
