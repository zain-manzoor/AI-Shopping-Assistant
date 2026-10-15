"""Terminal chat setup and local session identity tests."""

from __future__ import annotations

import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from agents.shopping_assistant import terminal


class TerminalTests(unittest.TestCase):
    def test_terminal_session_identity_is_created_once_and_reused(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            session_file = Path(temporary_directory) / ".adk" / "session_id"
            with patch.object(terminal, "SESSION_ID_FILE", session_file):
                first = terminal._get_terminal_session_id()
                second = terminal._get_terminal_session_id()

        self.assertEqual(first, second)
        self.assertEqual(str(uuid.UUID(first)), first)
