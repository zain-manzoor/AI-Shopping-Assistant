<!--
Sync Impact Report
- Version change: 1.0.0 -> 1.0.1 (clarified the simplicity rule to match its SHOULD-level intent)
- Modified principles: V. Architecture Boundaries (simplest-design rule: MUST -> SHOULD)
- Added sections: none
- Removed sections: none
- Follow-up TODO: confirm the original ratification date
-->

# AI Shopping Assistant Constitution

## Core Principles

### I. Spec-Driven Discipline
**Rationale:** Approved specifications keep implementation aligned with developer intent
and make decisions reviewable.

- MUST follow this workflow in order: constitution, specify, clarify, plan, tasks, analyze,
  implement.
- MUST have an approved specification, plan, and task before implementation begins.
- MUST update the specification, plan, tasks, and README in the same change as related code.
- MUST ask the developer to resolve ambiguity; MUST NOT silently assume missing requirements.

**Compliance is verified by:** reviewing the change for its approved artifacts, workflow
order, matching documentation updates, and recorded answers to material ambiguities.

### II. Learning First
**Rationale:** The developer is learning agent development, so each change must build
understanding while keeping the project runnable in small steps.

- MUST explain the concept introduced by each task (including ADK, MCP, SQL, or Python)
  before presenting its implementation.
- MUST deliver work in small, testable increments; MUST NOT deliver whole-project dumps.
- MUST begin with a single agent. Multiple agents MAY be introduced only after MCP integration
  is tested, and only when a specialist agent adds value over a plain tool.
- MUST teach MCP client and server roles and the complete request flow explicitly.

**Compliance is verified by:** checking task notes and change walkthroughs for the concept
explanation, incremental boundaries, agent-count rationale, and MCP flow description.

### III. Accuracy and No Fabrication
**Rationale:** Shopping decisions depend on correct catalog and cart information, and model
outputs must remain grounded in observable data.

- MUST obtain product data, prices, stock, specifications, and cart contents only from SQLite
  through tools; the model MUST NOT invent or infer these values.
- MUST state clearly when a tool returns no results or fails.
- MUST use APIs documented by official sources and current stable releases. MUST NOT invent APIs.
  Deprecated or experimental APIs require a written justification in the relevant plan.

**Compliance is verified by:** tracing shopping claims to tool results and checking API usage
against official documentation, including any required justification.

### IV. Security and Privacy
**Rationale:** Even a local simulated shop handles sensitive configuration and customer-scoped
state, so its boundaries must be explicit and enforced.

- MUST keep secrets only in `.env`; `.env.example` MUST contain placeholders only. `.env`,
  `*.db`, virtual environments, and caches MUST be git-ignored. Secrets MUST NOT be hardcoded.
- MUST parameterize every SQL statement, validate every tool argument, and use transactions
  and validation for state-changing operations.
- MUST receive customer identity from the application, never from model choice or invention.
  Each customer MUST access only their own cart and session data.
- MUST document that local session IDs do not provide real authentication.
- MUST keep shopping simulated. Real payment data, checkout, and payment processing are out
  of scope.
- MUST explain permissions and risks before using a third-party MCP server, and MUST use only
  servers assessed as trustworthy for the intended access.

**Compliance is verified by:** inspecting ignore rules and example configuration, reviewing
SQL and tool boundaries, testing customer isolation, checking documentation for the session
limitation and simulation scope, and reviewing third-party server risk notes.

### V. Architecture Boundaries
**Rationale:** Separating conversational context from durable records keeps the cart reliable
and the design understandable to a new agent developer.

- MUST keep ADK conversation sessions separate from durable SQLite data.
- MUST treat SQLite as the authoritative source for the cart; LLM history MUST NOT be treated
  as cart state.
- SHOULD choose the simplest design that meets the approved requirements, avoiding unnecessary
  files, layers, abstractions, and frameworks.

**Compliance is verified by:** tracing session and cart reads/writes to their owners and
reviewing each added layer or abstraction for a documented requirement.

### VI. Testing Standards
**Rationale:** Deterministic tests give fast feedback without paid model calls and cover the
failure cases that could mislead or harm a shopper.

- MUST provide deterministic unit and integration tests that run without paid LLM calls.
- MUST cover search, comparison (including missing products), cart operations, invalid IDs and
  quantities, insufficient stock, customer isolation, persistence across restarts, MCP tool
  behavior, ADK-to-MCP integration, and agent behavior on empty or error tool results.
- MAY provide Gemini-powered tests only as optional, separate, clearly marked tests.
- MUST pass the applicable tests before a task is considered done.

**Compliance is verified by:** running the deterministic test suite and mapping the required
scenarios to tests; confirming optional Gemini tests are separately marked.

### VII. Code Quality and Reproducibility
**Rationale:** Clear, repeatable practices help the developer learn and let another Windows
developer reproduce the project setup.

- MUST use Python type hints, docstrings on public functions, and English comments.
- MUST manage dependencies with `uv` and document reproducible setup in the README.
- MUST document PowerShell commands to run the project through `uv` and the ADK CLI.
- MUST use Ruff for linting and formatting, and pytest for tests.
- MUST build on the stated stack: Google ADK, Gemini API, official Python MCP SDK, SQLite,
  `python-dotenv`, and ADK Web. This constitution does not pin dependency versions.

**Compliance is verified by:** following the README setup in PowerShell, reviewing type hints
and public docstrings, and running the documented Ruff and pytest commands.

## Project Constraints

The application is a learning-oriented, production-minded shopping assistant. It uses Python,
Google ADK, the Gemini API, the official Python MCP SDK, SQLite, `uv`, `python-dotenv`, and
ADK Web. Development is performed on Windows with PowerShell and VS Code. No feature set or
pinned dependency versions are established by this constitution.

## Development Workflow

Every plan MUST include a **Constitution Check** gate that maps proposed work to applicable
principles and records any conflict before tasks are approved. Work proceeds through the
Spec-Driven Discipline sequence, and completion requires the applicable tests and coordinated
specification, plan, task, and README updates.

## Governance

This constitution governs project decisions and implementation. Plans and reviews MUST check
compliance with its principles. Amendments MUST be made in a reviewed change that updates this
file's semantic version and records the rationale in the change and Sync Impact Report.

- Increment MAJOR for incompatible governance changes, including removal or redefinition of a
  principle.
- Increment MINOR when adding a principle or materially expanding governance requirements.
- Increment PATCH for clarifications and non-semantic wording corrections.
- Every plan MUST contain and pass its Constitution Check gate before implementation tasks are
  approved. A conflict requires an explicit constitutional amendment or a documented plan
  revision before implementation.

**Version**: 1.0.1 | **Ratified**: TODO(RATIFICATION_DATE): confirm original adoption date | **Last Amended**: 2026-10-13
