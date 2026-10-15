# Research: AI Shopping Assistant

**Checked**: 2026-10-13. The workspace virtual environment is Python 3.14.4 and contains only pip 26.2.1; Google ADK, MCP, dotenv, pytest, and Ruff are not installed. Thus the exact APIs below are checked against official stable documentation and release/source metadata, not imports from this machine. During approved implementation, pin these versions in `uv.lock`, install them, and run the import/stdio smoke checks before relying on them. If a current release has changed, update this record and plan before implementation.

## Decisions and findings

### Stable package versions researched

| Package | Stable version researched | Use and evidence |
|---|---:|---|
| Python | 3.14.4 installed | Existing `.python-version` selects 3.14; `uv` environment reports Python 3.14.4. |
| `google-adk` | 2.11.0 | PyPI latest stable on check date; official Python ADK package. ADK 2.9 release notes state support for MCP SDK 1.x and 2.x. [PyPI](https://pypi.org/project/google-adk/) · [ADK releases](https://github.com/google/adk-python/releases) |
| `mcp` | 2.0.1 | Official Python MCP SDK stable 2.x. MCP SDK 2.x is a breaking line; use its `MCPServer` API, not the 1.x `FastMCP` name. [PyPI](https://pypi.org/project/mcp/) · [Python SDK docs](https://py.sdk.modelcontextprotocol.io/) · [v2 changelog](https://github.com/modelcontextprotocol/python-sdk/blob/main/CHANGELOG.md) |
| `google-genai` | 2.30.0 | Current stable PyPI release on check date. ADK invokes Gemini through its model integration; direct application imports may not be needed. [PyPI](https://pypi.org/project/google-genai/) |
| `python-dotenv` | 1.2.4 | Load local `.env` configuration. [PyPI](https://pypi.org/project/python-dotenv/) |
| `pytest` | 9.1.1 | Deterministic unit, contract, and integration tests. [PyPI](https://pypi.org/project/pytest/) |
| Ruff | 0.15.22 | Lint and format. [PyPI](https://pypi.org/project/ruff/) · [Ruff docs](https://docs.astral.sh/ruff/) |
| uv | 0.13.0 | Environment and dependency/lock management. [PyPI](https://pypi.org/project/uv/) · [uv docs](https://docs.astral.sh/uv/) |

SQLite is accessed via Python's standard-library `sqlite3`; it adds no third-party runtime package. Do not treat these researched latest versions as final pins until the task/implementation stage checks Python support, dependency resolution, and API compatibility together. The planned application code does not deliberately select a deprecated or experimental API.

### ADK ↔ MCP API

The current official ADK MCP tool guide uses:

```python
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters
```

Its stdio setup passes `connection_params=StdioConnectionParams(server_params=StdioServerParameters(command=..., args=[...]))` to `McpToolset`; the toolset manages the connection lifecycle and exposes server tools to the agent. `McpToolset` and `StdioConnectionParams` are the documented exact identifiers/imports. The installation-smoke test must verify them under the locked ADK/MCP versions. [Official ADK MCP tools guide](https://adk.dev/tools-custom/mcp-tools/) · [ADK Python API reference](https://adk.dev/api-reference/python/)

For customer identity, ADK documents `before_tool_callback(tool, args, tool_context)` as a `LlmAgent` callback. It can set/override tool arguments before dispatch. The application will place the selected demo ID in trusted session state, and the callback will always overwrite the `customer_id` argument for cart tools. Never accept a model's proposed ID. Environment variables on one stdio child are process-wide, which cannot safely distinguish concurrent customer calls to a shared server; explicit per-user child processes would add lifecycle complexity. [ADK callback types](https://adk.dev/callbacks/types-of-callbacks/) · [ADK MCP tools guide](https://adk.dev/tools-custom/mcp-tools/)

### MCP server / client / tool distinctions

- A **plain function** is ordinary Python behavior and is easiest to test directly.
- An MCP **tool** is a named, described, schema-bound operation exposed by an MCP server and callable via MCP protocol.
- The **MCP server** wraps those operations and, for this feature, handles JSON-RPC over stdio.
- The **MCP client** connects, discovers/calls tools, and receives results. ADK's `McpToolset` supplies this client role for the agent.

MCP SDK 2.x renamed its former `FastMCP` server class to `MCPServer` and moved the module from `mcp.server.fastmcp` to `mcp.server.mcpserver`. Its verified import is `from mcp.server.mcpserver import MCPServer`. The plan uses the SDK 2.x form. The ADK release notes document MCP SDK 2.x compatibility beginning with ADK 2.9.0. This is a current stable API, not an experimental API. [MCP SDK 2.x changelog](https://github.com/modelcontextprotocol/python-sdk/blob/main/CHANGELOG.md) · [ADK release notes](https://github.com/google/adk-python/releases)

### stdio child environment and secrets

The MCP Python SDK documents stdio child process environment as a minimal environment plus explicitly supplied variables. Provide only required interpreter/application paths and database configuration; do not pass `GOOGLE_API_KEY` or the parent process's full environment. Load the key from root `.env` only in the agent process, keep `.env` ignored, and commit `.env.example` with placeholder text. Inspect the resolved ADK transport implementation during installation smoke testing to confirm how it forwards `StdioServerParameters.env`. [MCP Python SDK client transports](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/client/transports.md)

### ADK Web discovery and sessions

The official Python quickstart shows an agent folder containing `agent.py`, `.env`, `__init__.py`, with the exported object named `root_agent`. Run `adk web` from the parent directory containing the agent folder; for this layout, `uv run adk web agents`. Official Web docs describe the default Python local session URI as per-agent SQLite at `<agents_dir>/<agent>/.adk/session.db`, artifacts in `.adk/artifacts`, and an in-memory alternative via `--no_use_local_storage`. Therefore resumed conversation state may persist across restarts; a newly created chat has new conversation state. Store durable carts independently in the application's `shopping.db`. Local session/customer IDs are not authentication. ADK Web is for development/debugging, not production. [ADK Python quickstart](https://adk.dev/get-started/python/) · [ADK Web interface](https://adk.dev/runtime/web-interface/)

### Testing without paid Gemini calls

Do not make live Gemini calls part of deterministic tests. Test plain functions and MCP tool handlers directly; test MCP stdio connection with a local test server; run the ADK agent with a scripted/fake model seam and assert tool requests/results. The installed packages were unavailable, so no test-only ADK model class name is prescribed here. During implementation, select a class/util only if documented by the locked ADK release and keep the test independent of a paid API. Separately mark any opt-in Gemini smoke tests and require explicit API-key configuration. This avoids inventing an ADK fake-model API.

### Data model and reservation approach

Use five relational tables required by the brief: `categories`, `products`, `customers`, `carts`, `cart_items`. Store prices as integer PKR minor units to avoid floating-point arithmetic; display with a PKR label. Product category fields are nullable columns with category-specific validation; this keeps the small fixed catalog inspectable without adding a schema abstraction. A cart line quantity is its stock reservation. Available stock equals on-hand stock less all cart line quantities. Reserve only the increase in the same serialized write transaction as cart mutation; release on decrease/removal. See [data-model.md](data-model.md).

## Alternatives considered

| Decision | Chosen | Alternative | Reason |
|---|---|---|---|
| ADK MCP connection | Official `McpToolset` over stdio | In-process Python functions only or HTTP transport | Spec requires MCP as a reusable boundary; stdio is local and ADK officially supports it. |
| SDK line | MCP 2.x with ADK 2.11.0 | MCP 1.x | Both supported per ADK 2.9+ release notes; 2.x is the current stable SDK line. Reconfirm resolution/imports because it is a major version. |
| Identity | Application session state plus per-call callback override | Trust model `customer_id`; one stdio process per customer with identity in environment | Callback override prevents model choice and supports shared-process concurrency; environment identity is static per child. |
| ADK conversation storage | ADK Web local SQLite | In-memory sessions | Supports Web session resumption; current conversation preferences remain attached to that conversation, while new chats start fresh. |
| Cart persistence | Separate SQLite database | ADK session history | Durable cart must be the single source of truth and independent of conversation history. |

## Open verification items

- Install exact releases in the chosen project root and confirm ADK/MCP import paths plus stdio server startup under Python 3.14.
- Confirm exact uv resolver support and dependency constraints together; update the lock/version table if resolution requires lower releases.
- Confirm the demo identity selector/mapping and implementation root before task breakdown.
- During tasks, validate the `MCPServer` decorator/start lifecycle against the official SDK documentation version matching the lock. Do not substitute a guessed example from SDK 1.x.

## Implementation verification update (2026-10-13)

The implementation root resolved and installed the pinned versions with Python 3.14.4: `google-adk` 2.11.0, `google-genai` 2.30.0, `mcp` 2.0.1, `python-dotenv` 1.2.4, `pytest` 9.1.1, and `ruff` 0.15.22. Imports of the documented ADK MCP classes and MCP SDK 2.x `MCPServer` succeeded. A real MCP stdio handshake listed all nine tools; ADK's `McpToolset` also launched the child and discovered those tools. ADK Web started and discovered the `shopping_assistant` root agent.

Runtime warning observed: ADK 2.11.0's `McpToolset` currently constructs its own deprecated internal `MCPTool` class (the warning recommends `McpTool`). The application does not import or instantiate that deprecated class directly; it uses the documented public `McpToolset` API, which is the required ADK integration boundary. ADK also emitted experimental-feature warnings for pluggable/authenticated-tool support and MCP graceful-error handling while importing/using this integration. The application does not configure or depend on those feature behaviors; they are enabled/reached internally by this ADK release. They are recorded here because the baseline avoids intentionally selecting experimental APIs, and should be revisited if a later stable ADK release removes these warnings.

The dependency lock is generated and `uv sync --locked --offline` succeeded. This workspace root has no Git metadata, so no commit could be created from this directory.
