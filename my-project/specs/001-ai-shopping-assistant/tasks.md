# Tasks: AI Shopping Assistant

**Input**: Design documents in `specs/001-ai-shopping-assistant/` (spec, plan, research, data model, MCP contract, quickstart)

**Implementation root**: `E:\TECH\Google adk`, following the recommended root in the approved `plan.md`.

**Tests**: Included because the specification and constitution require deterministic unit and integration tests without paid Gemini calls. Optional live Gemini checks remain separate and opt-in.

**Progress note**: Checkboxes are marked only for implementation and verification completed in this workspace. Unchecked ADK conversation and session-flow tasks remain outstanding. The workspace root has no Git metadata, so the lockfile is generated but cannot be committed here.

**Task format**: `- [ ] T### [P?] [US#?] Action, dependencies, requirement mapping, and exact file path(s)`

## Phase 1: Setup

**Purpose**: Establish a reproducible Windows/Python project without building the assistant yet.

- [x] T001 Create the planned `agents/shopping_assistant/`, `mcp_server/`, `shopping_data/`, `tests/unit/`, `tests/contract/`, and `tests/integration/` package directories with required `__init__.py` files under `E:\TECH\Google adk`.
- [x] T002 Add researched stable dependencies and development groups to `pyproject.toml`, resolve dependencies and generate `uv.lock`, and confirm Python 3.14 compatibility (depends on T001; versions and compatibility checks from `my-project/specs/001-ai-shopping-assistant/research.md`).
- [x] T003 Add `.env.example` with placeholder-only `GOOGLE_API_KEY` and non-secret local database settings, and update `.gitignore` to exclude `.env`, `*.db`, `.venv/`, caches, and `agents/shopping_assistant/.adk/` (depends on T001; FR-027, FR-028, FR-029).
- [x] T004 Configure Ruff lint/format and pytest defaults in `pyproject.toml`, including test discovery and markers for optional Gemini tests (depends on T002; SC-008, constitution VI–VII).
- [x] T005 [P] Write the local setup and environment safety instructions in `README.md`, including PowerShell/uv commands, placeholder-only env example, simulation limits, and the local customer ID authentication limitation (depends on T002–T003; FR-027–FR-029).

## Phase 2: Foundational (blocking prerequisites)

**Purpose**: Build shared persistence, configuration, identity, and MCP/ADK boundaries. No user-story phase starts until these foundations are usable.

- [x] T006 Define the five-table schema, foreign keys, uniqueness, category-specific field checks, nonnegative price/stock checks, and quantity bounds in `shopping_data/schema.sql` (depends on T001; data model; FR-006, FR-009, FR-013, FR-026).
- [x] T007 Implement SQLite connection setup, foreign-key enforcement, schema initialization, parameterized query helpers, and transaction/rollback helpers in `shopping_data/database.py` (depends on T006; FR-009, FR-010, FR-015).
- [x] T008 Add repeatable seed data for 40 fictional products and stable demo customer identities in `shopping_data/seed_catalog.py` (depends on T006–T007; FR-014, FR-026).
- [x] T009 Add root `.env` loading in the agent process and define an explicit minimal MCP child environment that omits `GOOGLE_API_KEY` in `agents/shopping_assistant/agent.py` (depends on T003; FR-028).
- [x] T010 Implement application-controlled demo customer selection/mapping and trusted customer ID storage at session creation in `agents/shopping_assistant/customer_context.py` (depends on T007–T008; FR-014, FR-015, FR-029).
- [x] T011 Define safe tool error mapping and redacted logging behavior in `mcp_server/tools.py` (depends on T007; FR-025, FR-028, FR-038; storage failures return a generic error, verified by the contract test).
- [x] T012 [P] Create deterministic database fixtures and temporary-database reset helpers in `tests/conftest.py` (depends on T007–T008; supports SC-001–SC-014).
- [x] T013 Implement the stdio MCP server entry point using the verified MCP 2.x server API and register tool handlers in `mcp_server/server.py` (depends on T002, T007, T011; MCP contract; FR-031).
- [x] T014 Create the single ADK shopping agent, official `McpToolset` stdio configuration, and allowlisted tool exposure in `agents/shopping_assistant/agent.py` (depends on T002, T009, T013; plan/research; FR-023, FR-028).
- [x] T015 Export `root_agent` from `agents/shopping_assistant/__init__.py` and add ADK Web-compatible agent metadata/instructions in `agents/shopping_assistant/agent.py` (depends on T014; plan; FR-023).
- [ ] T016 Add a documented scripted-model test seam using only APIs verified against the locked ADK release in `tests/conftest.py` (depends on T002, T014; constitution VI; no paid API calls).
- [x] T017 Write foundational schema, seed idempotence, parameterization, and rollback tests in `tests/unit/test_database.py` (depends on T006–T008; FR-026, SC-001, SC-004).
- [x] T018 Write a startup/stdio smoke test for MCP server launch, protocol handshake, and connection cleanup in `tests/integration/test_mcp_startup.py` (depends on T013–T015; MCP contract; no Gemini call).

**Checkpoint**: Project installs reproducibly; schema and seed initialize safely; MCP starts over stdio; ADK discovers its tools; no API key reaches the MCP child.

## Phase 3: User Story 1 — Search the catalog (Priority: P1)

**Goal**: Search the local catalog and present only accurate product details, including honest empty and unavailable results.

**Independent test**: A scripted conversation searches by name, category, inclusive price range, and catalog feature; returned IDs/prices/stock/specs match the 40 seeded products; invalid price range and zero results are clearly handled.

- [x] T019 [P] [US1] Write direct catalog query tests for name/category/price/feature filters, case-insensitive phrases, min-above-max rejection, ambiguous names, and zero matches in `tests/unit/test_catalog.py` (FR-001, FR-003–FR-005, FR-026).
- [x] T020 [P] [US1] Write MCP contract tests for `search_products`, `get_product_details`, `get_product_categories`, and `check_stock` result shapes and missing IDs in `tests/contract/test_tools_contract.py` (MCP contract; FR-001–FR-004, FR-026).
- [x] T021 [US1] Implement catalog search and current availability queries with bound SQL parameters in `shopping_data/catalog.py` (depends on T007–T008; FR-001, FR-004–FR-005, FR-026, FR-035).
- [x] T022 [US1] Implement the four catalog tool handlers with validated arguments and factual result payloads in `mcp_server/tools.py` (depends on T013, T021; MCP contract; FR-001–FR-005, FR-026, FR-035).
- [ ] T023 [US1] Add scripted ADK-to-MCP search flows for exact details, ambiguous names, invalid ranges, empty results, and out-of-stock labels in `tests/integration/test_search_conversation.py` (depends on T016, T022; FR-001–FR-005, FR-035; SC-001, SC-008).

**Checkpoint**: Search is independently usable, reports no-match honestly, and never makes up catalog facts.

## Phase 4: User Story 2 — Manage a personal cart (Priority: P1)

**Goal**: Add, update, remove, and view cart items with accurate totals and atomic stock reservations.

**Independent test**: Direct tool scenarios exercise valid changes, all invalid quantities/product IDs, stock contention, limits, empty/missing items, and a process/database restart; totals and reservations remain correct.

- [x] T024 [P] [US2] Write cart operation contract tests for success, stable rejection codes, empty cart, missing removal, and exact cart response totals in `tests/contract/test_tools_contract.py` (FR-006–FR-013, FR-033; SC-002, SC-005, SC-010–SC-011).
- [x] T025 [P] [US2] Write unit tests for add-as-increment, update-as-target-quantity, limits, invalid values, insufficient stock, release, and rollback in `tests/unit/test_cart.py` (FR-006–FR-012, FR-033; SC-002, SC-005, SC-010–SC-011).
- [x] T026 [US2] Implement cart creation/read/write helpers and customer-keyed cart/item queries in `shopping_data/cart.py` (depends on T007–T008; FR-006–FR-013).
- [x] T027 [US2] Implement atomic add/update/remove/view operations with `BEGIN IMMEDIATE`, reservation deltas, 10-unit and 20-product limits, and parameterized SQL in `shopping_data/cart.py` (depends on T026; FR-006–FR-013, FR-033; SC-002, SC-010–SC-011).
- [x] T028 [US2] Implement `add_to_cart`, `remove_from_cart`, `update_cart_quantity`, and `view_cart` handlers with validation and safe explanations in `mcp_server/tools.py` (depends on T027; MCP contract; FR-006–FR-013, FR-033).
- [x] T029 [US2] Add restart persistence and cart arithmetic integration tests using a new Python process and reopened database in `tests/integration/test_shopping_flows.py` (depends on T028; FR-007, FR-013; SC-002, SC-004).
- [ ] T030 [US2] Add realistic add/change/remove/view conversation scenarios, including invalid/non-numeric/huge quantity, unavailable stock, empty cart, and failure responses in `tests/integration/test_cart_conversation.py` (depends on T016, T028; FR-006–FR-012, FR-025, FR-033; SC-005, SC-008).

**Checkpoint**: Cart lines, totals, and stock reservations are authoritative in SQLite and survive restart.

## Phase 5: User Story 3 — Keep customer carts separate (Priority: P1)

**Goal**: Ensure application-selected identity scopes every cart operation and concurrent customers cannot see or reserve each other's data.

**Independent test**: Two app-created sessions use the same product concurrently; each sees only its own cart, reservations do not double-claim stock, and model-supplied identity attempts are overridden.

- [x] T031 [P] [US3] Write callback tests proving an application-sourced session customer ID overrides missing, forged, or conflicting tool arguments in `tests/unit/test_customer_identity.py` (depends on T010, T014; FR-014–FR-015; SC-003).
- [x] T032 [US3] Implement `before_tool_callback` identity injection/override for every cart tool in `agents/shopping_assistant/agent.py` (depends on T010, T014; FR-014–FR-015).
- [x] T033 Add simultaneous two-customer isolation and stock reservation tests in `tests/unit/test_cart.py` and `tests/integration/test_shopping_flows.py` (depends on T027?T032; FR-014?FR-015; SC-003, SC-010).
- [x] T034 [US3] Add a restart scenario proving the application reselects the same demo customer identity and restores only that customer's cart in `tests/integration/test_shopping_flows.py` (depends on T010, T029, T032; FR-013–FR-015, FR-029; SC-003–SC-004).

**Checkpoint**: Customer isolation is enforced and proven before recommendation or comparison features are added.

## Phase 6: User Story 4 — Compare products (Priority: P2)

**Goal**: Compare two to four catalog products and explain real price/spec/availability differences without fabricating missing items.

**Independent test**: Scripted comparisons cover two and four products, one product, over-limit requests, similar names, missing IDs, and unavailable items; all displayed facts match SQLite.

- [x] T035 [P] [US4] Write comparison contract and data tests for 2–4 IDs, duplicate/missing IDs, one-item and over-limit requests in `tests/contract/test_tools_contract.py` (FR-016–FR-017, FR-033; SC-001, SC-006).
- [x] T036 [US4] Implement comparison lookup using catalog detail and availability results in `shopping_data/catalog.py` (depends on T021; FR-016–FR-017, FR-035).
- [x] T037 [US4] Implement validated `compare_products` handler with missing-item markers and no invented values in `mcp_server/tools.py` (depends on T036; MCP contract; FR-016–FR-017).
- [ ] T038 [US4] Add scripted agent comparisons, including stated-needs/budget explanations and partial results for missing products, in `tests/integration/test_comparison_conversation.py` (depends on T016, T037; FR-016–FR-017, FR-025, FR-034–FR-035; SC-001, SC-006).

**Checkpoint**: Comparison is independently testable, within the four-item cap, and grounded in catalog responses.

## Phase 7: User Story 5 — Get personalized recommendations (Priority: P2)

**Goal**: Remember criteria within a conversation, respect a hard budget, ask one useful question at a time, and recommend only available catalog products not rejected, owned, or carted.

**Independent test**: Scripted conversations verify remembered criteria, no repeated questions, conflict clarification, strict budget, unavailable exclusions, cart exclusions, rejection/ownership memory, and no suitable results.

- [ ] T039 [P] [US5] Write scripted recommendation cases for budget limits, criteria memory, one-at-a-time clarifications, conflicting preferences, out-of-stock products, cart items, rejected/owned products, and no match in `tests/integration/test_recommendation_conversation.py` (FR-018–FR-021, FR-032, FR-034–FR-037; SC-006–SC-007, SC-012–SC-013).
- [x] T040 [US5] Define and implement conversation-scoped criteria, rejected IDs, declared-owned IDs, and reset behavior for a new conversation in `agents/shopping_assistant/conversation_state.py` (depends on T014; FR-018, FR-020–FR-022, FR-032, FR-037; deterministic helper tests in `tests/unit/test_conversation_state.py`).
- [ ] T041 [US5] Implement recommendation instructions/flow that searches only catalog tools, treats budget as a strict ceiling, filters zero-stock/carted/rejected/owned products, and asks one relevant question per turn in `agents/shopping_assistant/agent.py` (depends on T021–T022, T027–T028, T040; FR-018–FR-021, FR-032, FR-034–FR-037).
- [ ] T042 [US5] Add resume-versus-new-conversation and cross-customer memory-isolation tests in `tests/integration/test_conversation_memory.py` (depends on T032, T040–T041; FR-014–FR-015, FR-018, FR-020, FR-037; SC-003, SC-007, SC-013).

**Checkpoint**: Recommendations honor every stated criterion using catalog/cart facts and conversation-local memory only.

## Phase 8: User Story 6 — Shop through natural conversation (Priority: P2)

**Goal**: Provide concise free-text routing, clarification, scope redirection, and honest handling of model/tool failures through ADK Web.

**Independent test**: Run scripted shopping, ambiguous, unrelated, checkout, empty-result, tool-failure, and model-service-failure conversations without live Gemini; run the local Web interface manually with an opt-in key.

- [ ] T043 [P] [US6] Write scripted natural-language routing and one-question clarification tests in `tests/integration/test_natural_conversation.py` (depends on T016; FR-023–FR-024; SC-008).
- [ ] T044 [P] [US6] Write model-service/tool-error scenarios asserting no unsupported claims and no repeated uncertain cart mutation in `tests/integration/test_service_failures.py` (depends on T016; FR-025, FR-038; SC-008, SC-014).
- [x] T045 [US6] Add assistant behavior instructions for concise shopping-only replies, checkout/payment refusal, unrelated-topic redirect, honest tool failure, and uncertain-mutation handling in `agents/shopping_assistant/agent.py` (depends on T014, T022, T028, T041; FR-023–FR-025, FR-038).
- [x] T046 [US6] Configure local Gemini model selection and API-key loading from `.env` in `agents/shopping_assistant/agent.py`; confirm the key is not logged or forwarded to the MCP child (depends on T009, T014; FR-028).
- [ ] T047 [US6] Configure and validate ADK Web discovery/session behavior, agent root export, local persistence, and new-chat state reset in `agents/shopping_assistant/__init__.py` and `tests/integration/test_adk_web_session.py` (depends on T015, T040; FR-014, FR-037; SC-013).
- [x] T048 [US6] Document startup and manual Web scenarios, local session persistence, customer selector limitation, env setup, and simulation scope in `my-project/specs/001-ai-shopping-assistant/quickstart.md` and `README.md` (depends on T045–T047; FR-027–FR-029).
- [ ] T049 [US6] Add separately marked opt-in Gemini smoke tests and skip-by-default configuration in `tests/integration/test_gemini_optional.py` and `pyproject.toml` (depends on T046; FR-025, FR-038; optional only, never part of deterministic acceptance).

**Checkpoint**: Free-text experience is usable in ADK Web; deterministic acceptance does not require a Gemini API call.

## Phase 9: User Story 7 — Use one assistant before specialist collaboration (Priority: P3, later phase)

**Goal**: Preserve baseline behavior if specialist collaboration is approved after the single-agent release is tested.

**Gate**: Do not begin this phase until Phases 1–8 pass and a follow-on plan/task set is approved. The current technical plan intentionally outlines this phase only.

- [ ] T050 [US7] Record baseline acceptance results and identify flows suitable for specialist collaboration in `my-project/specs/001-ai-shopping-assistant/plan.md` (depends on all MVP story checkpoints; FR-030).
- [ ] T051 [US7] Create an approved follow-on design and task list defining coordinator/search/comparison/recommendation/cart responsibilities and customer identity propagation in `my-project/specs/001-ai-shopping-assistant/plan.md` and `my-project/specs/001-ai-shopping-assistant/tasks.md` (depends on T050; FR-030; no specialist agents are created in the MVP task set).
- [ ] T052 [US7] Add regression scenarios that run the existing acceptance suite against the approved collaborative flow in `tests/integration/test_specialist_regression.py` (depends on T051 and the separately approved specialist implementation tasks; FR-030; SC-008).

## Phase 10: User Story 8 — Reuse shopping capabilities (Priority: P3, optional extension)

**Goal**: Keep catalog/cart tools reusable by MCP clients while deferring third-party server use until a source and permissions are reviewed.

**Gate**: Baseline first-party MCP tool contracts and acceptance tests must pass. No third-party server or extra-client integration is part of the MVP.

- [ ] T053 [US8] Review the first-party MCP contract for stable schemas, validation, customer scoping, and source attribution requirements in `my-project/specs/001-ai-shopping-assistant/contracts/shopping-tools.md` (depends on T018, T022, T028, T033; FR-031).
- [ ] T054 [US8] Write a separate approved extension plan before selecting or connecting any third-party MCP server, including trust evidence, requested permissions, data exposure, and failure behavior in `my-project/specs/001-ai-shopping-assistant/research.md` (depends on T053; FR-031; constitution IV).
- [ ] T055 [US8] After the extension plan is approved, add another-client contract tests for catalog/cart parity and customer isolation in `tests/contract/test_external_client_parity.py` (depends on T054 and separately approved client integration tasks; FR-031; SC-003, SC-008).

## Phase 11: Polish and cross-cutting validation

**Purpose**: Validate all accepted stories, safe configuration, reproducibility, and learner documentation.

- [ ] T056 [P] Add complete scripted acceptance scenarios mapped to every delivered story in `tests/integration/test_acceptance_scenarios.py` (depends on T023, T030, T033–T034, T038, T042, T043–T047; SC-001–SC-014).
- [ ] T057 Verify each requirement maps to one or more automated tests and document the mapping in `my-project/specs/001-ai-shopping-assistant/quickstart.md` (depends on T056; FR-001–FR-038, SC-001–SC-014).
- [ ] T058 Review logs, exception messages, `.gitignore`, `.env.example`, and MCP child environment for secret/path/identity leakage in `tests/integration/test_security_boundaries.py` (depends on T003, T009, T010, T013–T015, T046; FR-014–FR-015, FR-028–FR-029; SC-003, SC-009).
- [ ] T059 Run the documented deterministic suite, Ruff lint/format checks, and PowerShell quickstart validation; fix failures in their owning files and record outcomes in `README.md` (depends on all MVP stories and T056–T058; constitution VI–VII).

## Dependencies and Execution Order

### Phase dependencies

- Setup (T001–T005) precedes foundational work.
- Foundation (T006–T018) blocks all story implementation because database, identity, MCP transport, and ADK tool discovery are shared prerequisites.
- P1 story order: Search (US1) can proceed after the foundation; Cart (US2) also relies on the shared schema; Customer separation (US3) depends on cart behavior and identity injection. Finish and verify all three before P2 work.
- P2 stories: Comparison (US4) uses catalog search/details; Recommendations (US5) uses catalog, cart, and identity; Natural conversation (US6) integrates the completed flows and Web runtime.
- US7/US8 are gated later phases; they require a separate approved plan before implementation.
- Polish T056–T059 follows the MVP stories. Optional Gemini checks do not gate deterministic acceptance.

### User story dependencies

| Story | Can start after | Depends on |
|---|---|---|
| US1 Search (P1) | Foundation | Shared catalog/database/MCP/ADK setup |
| US2 Cart (P1) | Foundation | Database schema and transaction helpers |
| US3 Customer separation (P1) | US2 cart operations | Application identity and cart mutation boundary |
| US4 Comparison (P2) | US1 | Catalog detail and availability queries |
| US5 Recommendations (P2) | US1, US2, US3 | Catalog, cart view, identity, session state |
| US6 Natural conversation (P2) | US1–US5 | Agent instructions, failures, session behavior |
| US7 Specialist collaboration (P3) | Tested MVP and separately approved follow-on plan | Baseline regression suite |
| US8 Client reuse (P3 optional) | Tested first-party MCP tools and separately approved extension plan | Contract parity and trust review |

## Parallel opportunities

- Setup T005 can proceed beside T002–T004 after T001 because it touches README only.
- Foundation T009 and T012 can proceed in parallel once their stated dependencies are ready; they touch config and test fixtures respectively.
- US1 T019 and T020 are independent test files and can be authored in parallel before implementation.
- US2 T024 and T025 can be authored in parallel; cart implementation tasks remain sequential because reservation operations share `shopping_data/cart.py`.
- US3 T031 may be authored alongside US3 integration test planning, but the integration test depends on the callback and cart foundation.
- US4 T035 is independent of `shopping_data/catalog.py` implementation until integration.
- US5 T039 can be authored before conversation-state implementation; implementation and agent instruction tasks share dependencies and should be sequential.
- US6 T043 and T044 can be authored in parallel in separate files; T045–T047 share agent/session setup and are sequential where indicated.
- Polish security review T058 may run alongside T057 after the MVP is complete; final validation T059 waits for both.
- No user stories are parallelized across implementers by default because they modify shared `agent.py`, `mcp_server/tools.py`, and SQLite interfaces.

## Parallel Example: User Story 1

```text
After Foundation is complete, author these independent tests in parallel:
T019 tests/unit/test_catalog.py
T020 tests/contract/test_tools_contract.py

Then implement sequentially:
T021 shopping_data/catalog.py
T022 mcp_server/tools.py
T023 tests/integration/test_search_conversation.py
```

## Implementation Strategy

### MVP first

1. Complete Setup and Foundation.
2. Deliver US1 Search, US2 Cart, and US3 Customer separation (P1), running each story's deterministic tests before proceeding.
3. Stop at the P1 checkpoint and validate accurate catalog data, persistence, stock reservation, and isolation.
4. Add US4 Comparison, US5 Recommendations, and US6 Natural conversation (P2), retaining no-paid-call deterministic tests.
5. Run Polish validation. Treat this as the first complete assistant release.
6. Do not implement US7 specialists or US8 external/client extensions until their gates and follow-on plans are approved.

### Test-first increments

Within each story, write the listed tests first, confirm they fail for the intended missing behavior when implementation begins, then implement the smallest path to green. Never run live Gemini calls in the required acceptance suite. Every task introduces a concept in its implementation walkthrough (Python project/uv, SQLite transaction, MCP server/client/tool flow, or ADK session/agent) as required by the constitution.

## Notes

- `[P]` means the task edits distinct files and has no dependency on unfinished work. Story labels map to the spec's eight user stories.
- Cart tool `customer_id` values are overridden from application/session state before dispatch; model-provided identity is never trusted.
- The MCP child receives an explicit allowlist; it must not receive `GOOGLE_API_KEY`.
- Catalog data and stock are local fictional data. No external source is consulted in the MVP.
- Task paths are relative to `E:\TECH\Google adk` except specification/design artifact paths, which are relative to the spec-kit root `E:\TECH\Google adk\my-project`.
