"""Interactive terminal client for the ADK shopping agent."""

from __future__ import annotations

import asyncio
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SESSION_ID_FILE = Path(__file__).resolve().parent / ".adk" / "terminal_session_id"


def _get_terminal_session_id() -> str:
    """Reuse an app-generated local identity so the cart is reachable next launch."""
    SESSION_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        session_id = str(uuid.UUID(SESSION_ID_FILE.read_text(encoding="utf-8").strip()))
    except FileNotFoundError:
        session_id = str(uuid.uuid4())
        SESSION_ID_FILE.write_text(session_id, encoding="utf-8")
    except ValueError:
        session_id = str(uuid.uuid4())
        SESSION_ID_FILE.write_text(session_id, encoding="utf-8")
    return session_id


async def run_terminal_chat() -> int:
    """Run a text chat using the same agent and MCP tools as ADK Web."""
    load_dotenv(PROJECT_ROOT / ".env")
    if not os.getenv("GOOGLE_API_KEY"):
        print("Set GOOGLE_API_KEY in the project .env file before starting a chat.")
        return 1

    database_path = Path(os.getenv("SHOPPING_DB_PATH", "shopping.db")).expanduser()
    if not database_path.is_absolute():
        database_path = PROJECT_ROOT / database_path
    if not database_path.is_file():
        print("The local catalog is not initialized. Run: uv run python main.py seed")
        return 1

    from agents.shopping_assistant import root_agent

    session_id = _get_terminal_session_id()
    session_service = InMemorySessionService()
    runner = Runner(
        app_name=root_agent.name,
        agent=root_agent,
        session_service=session_service,
    )
    await session_service.create_session(
        app_name=root_agent.name,
        user_id="terminal-user",
        session_id=session_id,
    )

    print("AI Shopping Assistant — terminal chat")
    print("Type :quit or press Ctrl+C to end. Your cart remains saved in SQLite.")
    print("This launch starts fresh conversation preferences for the same local demo customer.")
    try:
        while True:
            try:
                message = await asyncio.to_thread(input, "\nYou> ")
            except EOFError:
                break
            if message.strip().casefold() in {":quit", ":q", "/exit"}:
                break
            if not message.strip():
                continue

            request = types.Content(
                role="user",
                parts=[types.Part.from_text(text=message.strip())],
            )
            try:
                async for event in runner.run_async(
                    user_id="terminal-user",
                    session_id=session_id,
                    new_message=request,
                ):
                    if not event.is_final_response() or event.content is None:
                        continue
                    response = "".join(
                        part.text or "" for part in event.content.parts or [] if part.text
                    )
                    if response:
                        print(f"\nAssistant> {response}")
            except Exception:
                print("\nAssistant> I couldn't complete that request. Please try again.")
    except KeyboardInterrupt:
        print("\nChat ended.")
    finally:
        await runner.close()
    return 0
