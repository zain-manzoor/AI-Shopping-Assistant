# Implementation Plan: AI Shopping Assistant

**Branch**: `001-ai-shopping-assistant` | **Date**: 2026-10-13 | **Spec**: [spec.md](spec.md)

## Summary

Deliver the clarified shopping experience incrementally: first a single conversational assistant for the 40-item fictional catalog, comparison, recommendations, and customer-scoped shopping cart. The assistant calls catalog and cart capabilities through an official MCP stdio connection; SQLite owns catalog, customer, cart, and stock-reservation facts. Conversation preferences live only in the ADK conversation session. Checkout, payment, specialist collaboration, third-party MCP use, and another-client reuse remain later/out-of-scope phases. See [research.md](research.md), [data-model.md](data-model.md), [contracts/shopping-tools.md](contracts/shopping-tools.md), and [quickstart.md](quickstart.md).

## Technical Context

**Language/Version**: Python 3.14 (existing `.python-version`; environment has Python 3.14.4)
**Primary Dependencies**: `google-adk` 2.11.0; official `mcp` SDK 2.0.1; `google-genai` 2.30.0; `python-dotenv` 1.2.4; `pytest` 9.1.1; Ruff 0.15.22; uv 0.13.0. Versions and sources are recorded in [research.md](research.md). These packages are not installed in the current `.venv`; the exact imports below are verified against current official docs/release metadata, not an installed environment. Confirm the resolved lock and import smoke tests when implementation is approved.
**Storage**: SQLite via Python's standard-library `sqlite3`; catalog, customer identities, carts, cart lines, and reservations are durable. ADK Web local SQLite session storage retains conversation sessions for resumption. New conversations start fresh preference/rejection/ownership memory.
**Testing**: pytest; deterministic database, direct MCP-tool, agent-to-MCP, failure, isolation, and restart tests without paid model calls. Gemini tests are optional and separately marked.
**Target Platform**: Windows / PowerShell, local development with ADK Web; not production deployment.
**Project Type**: Single Python project with one ADK agent and a separately launched stdio MCP server process.
**Performance Goals**: No latency target stated; prioritize deterministic correctness for a 40-product local catalog and concurrent demo customers.
**Constraints**: PKR prices; up to 10 units per product and 20 distinct cart lines; compare 2–4 products; identity supplied by the host application; no real accounts, payment, checkout, shipping, or real personal data. Tools validate arguments and use parameterized SQL and transactions.
**Scale/Scope**: Local learning demo, 40 fictional products, fixed demo customer identities, single-agent first. Specialist agents and capability reuse are later phases only.

## Constitution Check

### Gate before research

| Principle | Plan check |
|---|---|
| I. Spec-Driven Discipline | Clarified spec is Ready for planning. This plan defines design only; implementation waits for approved plan and later tasks. |
| II. Learning First | Start with one agent; describe the full MCP client/server/tool flow in plan and quickstart. Add specialists only after single-agent tests pass. |
| III. Accuracy and No Fabrication | Product facts and cart values come only from catalog/cart tools backed by SQLite. Empty results and tool failures are reported plainly. Avoid deprecated APIs; current release docs are cited in research. |
| IV. Security and Privacy | Host-selected stable demo identity is injected into every cart tool call; model arguments cannot choose it. Isolate cart reads/writes; keep secrets in root `.env`, ignored by Git; MCP child receives an explicit allowlist without Gemini key. Document local IDs are not authentication. |
| V. Architecture Boundaries | ADK session state stores conversation-only criteria, rejections, and declared ownership. SQLite is the cart and reservation source of truth. Keep direct DB services simple; no unneeded layers. |
| VI. Testing Standards | Deterministic tests cover catalog/cart, MCP, ADK-to-MCP, invalid inputs, empty/error results, concurrency isolation, and restart persistence. Paid Gemini tests are optional. |
| VII. Code Quality and Reproducibility | Use uv, type hints, public docstrings, Ruff, pytest, PowerShell commands, `.env.example`, and reproducible setup. |

**Pre-research gate: PASS.** No conflict with the constitution. Current environment lacks project dependencies, so release-specific behavior will be install-smoke-tested before implementation. No experimental or deprecated API is planned.

## Design Decisions

1. **MCP boundary and flow.** Plain Python functions implement the catalog/cart operations. The MCP server registers those functions as MCP tools and serves them over stdio. The ADK `McpToolset` is the MCP client: it starts/connects to that server process, discovers allowed tools, and forwards tool calls/results. This makes reusable capabilities available across compatible clients without making a normal Python function itself “an MCP tool.” ADK uses the documented imports `google.adk.tools.mcp_tool.McpToolset`, `google.adk.tools.mcp_tool.mcp_session_manager.StdioConnectionParams`, and `mcp.StdioServerParameters`. Pin to MCP SDK 2.x and use its documented `MCPServer` API; the ADK release notes say ADK 2.9 added support for both MCP SDK 1.x and 2.x.
2. **Identity.** The application selects/assigns the stable local demo customer ID and attaches it to trusted ADK session state when creating a session. An ADK `before_tool_callback(tool, args, tool_context)` overwrites/injects that value on every cart tool call. The MCP server requires the ID but does not trust an LLM-provided one. This supports simultaneous sessions while avoiding per-user stdio process restarts. A model-supplied ID is unsafe because a prompt could name another customer; relying on it would let the model choose whose cart a tool accesses. Transport environment identity is supported but fixed per child process, which is a poor fit for concurrent customers sharing one agent process. Isolation tests use two application-created sessions and deliberately hostile/mismatched model arguments, including concurrent cart operations.
3. **Stock reservation.** A cart quantity is a reservation, not a decrement of physical catalog stock. In one write transaction, calculate unreserved quantity as on-hand stock minus quantities in all carts, then reserve only the increase. Decreases/removals release it. `BEGIN IMMEDIATE` serializes local SQLite writers so concurrent customers cannot reserve the same units. Cart read/change checks use current catalog facts. External stock changes are outside the initial app surface; if introduced later, the plan must define behavior when on-hand stock falls below existing reservations.
4. **ADK Web persistence.** Run Web from the folder containing the ADK agent package. Python ADK Web discovers an agent package containing `agent.py` and an exported `root_agent`. Its default local session service stores sessions in per-agent `.adk/session.db` and artifacts under `.adk/artifacts`; therefore resumed conversations can retain their session history/state across process restarts. A new chat/session has fresh recommendation memory. Durable carts are in a separate application SQLite file and keyed by the application-selected demo customer, independent of chat/session IDs. This makes explicit that session ID is not authentication.
5. **Later phases only.** Outline (do not implement first): after baseline acceptance scripts pass, evaluate coordinator plus search/comparison/recommendation/cart specialists against the same scripted behavior; optionally connect an independently reviewed third-party MCP server with least privilege and clear source attribution; optionally expose the local capabilities to another compatible MCP client. Each extension requires its own approved tasks and trust/compatibility checks.

## Project Structure

Implementation target is the workspace root containing `pyproject.toml`, `.python-version`, and `main.py`; spec-kit artifacts are currently under `my-project/specs/...`. That split is an approval item in “Risks, Unknowns, and Decisions,” since `AI-Shopping-Assistant/` is also present as an empty Git checkout.

```text
<implementation-root>/
├── .env                         # local secret; ignored
├── .env.example                 # placeholders only
├── .gitignore
├── pyproject.toml               # uv dependencies, tool config
├── uv.lock
├── agents/
│   └── shopping_assistant/      # ADK Web discovers this package
│       ├── __init__.py          # exports root_agent
│       ├── agent.py             # single LlmAgent + MCP toolset
│       └── .adk/                # local ADK session DB/artifacts; ignored
├── mcp_server/
│   ├── __init__.py
│   ├── server.py                # stdio MCP entry point and tool registration
│   └── tools.py                 # plain Python catalog/cart tool functions
├── shopping_data/
│   ├── __init__.py
│   ├── database.py              # connections, schema setup, transactions
│   ├── catalog.py               # catalog queries
│   ├── cart.py                  # cart/reservation operations
│   ├── schema.sql
│   └── seed_catalog.py          # 40 fictional products
└── tests/
    ├── unit/
    ├── contract/
    └── integration/

my-project/specs/001-ai-shopping-assistant/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/shopping-tools.md
```

**Structure Decision**: A single Python distribution with distinct agent, MCP server, and data modules. ADK Web is run from `<implementation-root>` with `uv run adk web agents`; its `agents/shopping_assistant/agent.py` package exports `root_agent`. ADK's `McpToolset` auto-starts the MCP server over stdio when the agent connects, so no second terminal/process is needed in the normal flow. The MCP entry point remains independently launchable for direct development and tests.

## Constitution Check (post-design)

**PASS, with approval items below.** Single-agent-first sequencing, the required MCP boundary, authoritative SQLite cart state, session/data separation, application-controlled identity, secrets boundary, simulated scope, and deterministic acceptance tests are all represented. The MCP SDK 2.x choice is supported by ADK 2.9+ release notes. No deprecated/experimental API is proposed. Before implementation, resolve the root/checkout ambiguity and install the documented stable packages into the project environment; smoke-check exact imports and stdio startup against the locked versions. If they differ, update research and plan before tasks.

## Risks, Unknowns, and Decisions for Approval

1. **Repository root (decision):** recommended implementation root is `E:\TECH\Google adk` because it has the current uv project and Python environment. `AI-Shopping-Assistant/` is a separate empty Git checkout, while spec-kit files live in `my-project/`. Approve which folder should contain implementation and whether the spec artifacts should be copied/moved into that repo before tasks.
2. **Dependency installation (decision):** this workspace's `.venv` has Python 3.14.4 and pip only; the listed package versions are research targets, not installed versions. Approve installing and locking the current stable versions at the task/implementation stage after this plan.
3. **Identity presentation (unknown):** the clarified spec says the app assigns and reuses an ID but does not define the UI that chooses among demo customers or maps a returning local user to one. The recommended demo is a small application-controlled customer selector with a stable local mapping, clearly labeled as not authentication. Decide its exact presentation before implementation tasks.
4. **Session retention (decision):** the recommended default uses ADK Web local SQLite session storage, so a resumed chat's session memory persists across process restarts; new chats begin with clean conversation preferences. If that retention is unwanted, use in-memory ADK sessions, understanding restart loses conversation state while carts still persist.
5. **Catalog field types / formatting (approval):** plan recommends exact PKR minor-unit integer storage and category-specific nullable spec columns. The spec fixes categories and facts but not numeric precision, rounding, or display grouping. Confirm this simple representation during tasks; no payments are involved.
6. **Concurrent reservation edge (risk):** SQLite transactions prevent two local cart operations from claiming the same available quantity. If catalog stock is externally reduced below already-reserved cart quantities, spec behavior is not defined because no stock-edit interface exists; no such edit is in the initial feature.
7. **ADK version currency (risk):** 2.11.0 is the current PyPI stable release as checked 2026-10-13, but newer releases may appear before implementation. Re-check and lock versions then; only change versions with updated official-source evidence and compatibility checks.

## Complexity Tracking

No Constitution Check violations. SQLite reservation transactions and identity injection are required by the clarified behavior and do not add unnecessary architecture.
