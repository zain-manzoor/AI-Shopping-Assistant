# Quickstart and Validation Guide

Run these commands from the implementation root, `E:\TECH\Google adk`, using Windows PowerShell. ADK Web is a local development interface, not a production service.

## Setup

```powershell
Copy-Item .env.example .env
# Edit .env and set GOOGLE_API_KEY to your Gemini API key.
uv sync
uv run python main.py seed
```

Keep the real key in the ignored root `.env`. The committed `.env.example` contains placeholders only. The ADK process loads `.env`; its MCP child receives an explicit minimal environment that excludes `GOOGLE_API_KEY`. Do not enter real personal or payment data. This demo does not need it.

The seed command creates four categories, 40 fictional products, and stable demo identities. Reseeding refreshes fictional catalog rows without deleting carts. The local `shopping.db` contains catalog, demo customer IDs, carts, and cart items. Prices are stored as integer paisa and displayed in PKR.

## Run the assistant

```powershell
uv run adk web agents
```

Open the local URL printed by ADK Web and select `shopping_assistant`. The `agents/shopping_assistant/` package exports `root_agent`. ADK's official MCP toolset starts the custom server over stdio; a separate MCP terminal is not needed. To inspect that server independently, run `uv run python -m mcp_server`; it waits for a client and uses stdout for protocol traffic.

For terminal chat instead of the Web interface, run:

```powershell
uv run python main.py chat
```

Enter a message at `You>` and type `:quit` to end the chat. The CLI uses the same ADK agent and MCP tools. It reuses a locally stored application-generated session ID for the same cart identity, while conversation preferences reset on each CLI launch.

ADK Web's local session storage preserves a conversation for resumption. Preferences, rejections, and declared-owned products live in that conversation state. A new chat starts fresh conversation state. The cart and reserved stock are durable in `shopping.db`. The application maps the ADK-created session ID to an opaque local demo customer ID. This is a local session boundary, not real authentication.

With a valid Gemini API key configured, try these manual Web scenarios:

- Search: “Find an in-stock electronics product under PKR 200,000.”
- Compare: “Compare EL-001 and EL-002 for my budget and intended use.”
- Cart: “Add one EL-001 to my cart, then show the cart total.”
- Recommendations: state a budget and required feature, reject one suggestion, then ask for another.
- Scope handling: ask to check out or ask an unrelated question and confirm the assistant redirects without claiming a purchase.

## Deterministic checks

```powershell
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Tests use temporary SQLite databases and do not call Gemini. They cover catalog and cart data operations, validation, stock reservation, cart persistence read by a new Python process, customer isolation, identity override, and the real MCP stdio handshake/tool call. ADK Web startup and agent discovery were also verified locally. Full scripted customer-facing conversations through ADK, including live tool-error and Gemini-error turns, are not yet covered by deterministic tests. No live Gemini smoke test is included.

## Scope

This implementation uses the fictional local catalog only. No external product source is connected. Checkout, payments, shipping, real accounts, authentication, and production deployment are out of scope. Specialist-agent collaboration and client reuse are gated follow-on work.
