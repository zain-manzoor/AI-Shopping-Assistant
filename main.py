"""Local data and terminal commands for the AI Shopping Assistant."""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Sequence

from shopping_data.database import connect, initialize
from shopping_data.seed_catalog import seed_catalog


def seed() -> None:
    """Create the schema and seed the fictional catalog and demo identities."""
    connection = connect()
    try:
        initialize(connection)
        seed_catalog(connection)
    finally:
        connection.close()


def main(argv: Sequence[str] | None = None) -> int:
    """Run a local data or terminal-chat command."""
    parser = argparse.ArgumentParser(description="AI Shopping Assistant local commands")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("seed", help="initialize and seed the local fictional catalog")
    subparsers.add_parser("chat", help="chat with the assistant in this terminal")
    arguments = parser.parse_args(argv)

    if arguments.command == "seed":
        seed()
        print("Local catalog ready: 40 fictional products across 4 categories.")
        return 0

    from agents.shopping_assistant.terminal import run_terminal_chat

    return asyncio.run(run_terminal_chat())


if __name__ == "__main__":
    raise SystemExit(main())
