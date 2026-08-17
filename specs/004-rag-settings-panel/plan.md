# Implementation Plan: RAG Settings Panel

**Branch**: `004-rag-settings-panel` | **Date**: 2026-08-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-rag-settings-panel/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

Add a per-conversation `conversation_settings` model (`web_search_enabled`, `temperature`,
`retrieval_top_k`, `included_document_types`) stored in Supabase Postgres and read by the
FastAPI backend on every `ask` request (003-rag-project-chat) when assembling retrieval and
generation parameters. When `web_search_enabled` is true, the existing LangGraph retrieval
flow gains a conditional routing node that decides whether to supplement project-document
context with live web search results before generation. The frontend adds a collapsible
right-hand settings panel, built from the same glass-panel design-system primitives
(001-core-foundation), whose controls update conversation state immediately (no reload) and
persist each change to the backend as it happens.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.x (frontend, Next.js App Router —
reused from prior slices)

**Primary Dependencies**: FastAPI, Pydantic v2 (settings schema/validation), LangGraph
(extended with a conditional web-search routing node, reusing the graph from
003-rag-project-chat/002-document-processing-pipeline), a web search tool/API client (invoked
only when `web_search_enabled` is true), Supabase Python client (Postgres), React state
(Next.js) + the existing design-system glass-panel components (001-core-foundation) for the
frontend panel

**Storage**: Supabase Postgres — new `conversation_settings` table, one row per conversation
thread, read (not duplicated) by the retrieval/generation pipeline from
003-rag-project-chat on each `ask` call

**Testing**: `pytest` for settings-read/validation unit tests, LangGraph routing-node unit
tests (web-search branch taken/not-taken), integration tests (settings persisted then applied
to the next question, in-flight generation unaffected by concurrent setting changes,
document-type filter narrows citations); Vitest/Jest + Playwright for panel discoverability,
immediate-apply-without-reload behavior, and persistence-on-reopen

**Target Platform**: Same web application as prior slices

**Project Type**: Web application (frontend + backend) — extends `backend/` and `frontend/`
from 001–003

**Performance Goals**: Setting changes apply to the next question with no added latency
beyond a normal question (SC-006); panel discoverable/openable without added page-load cost

**Constraints**: A setting change MUST NOT alter an answer already generating when the change
occurs (constitution Principle VII consistency; FR-013); previously delivered answers/citations
MUST remain unchanged after a later setting change (FR-014); all settings reads/writes MUST be
scoped to the owning user's project/conversation (constitution Principle I; FR-017); the panel
MUST reuse the existing Liquid Glass design system and light/dark theming, not introduce new
styling (constitution Principle VI; FR-016); web search, when enabled, must still preserve
citation/traceability expectations for any external content used (constitution Principle II;
FR-005)

**Scale/Scope**: One settings row per conversation thread; this slice only adds the settings
model, the web-search routing decision point, and the panel UI — it does not implement a full
web-search retrieval/summarization pipeline beyond what's needed to supplement chat context
(no new document ingestion, no persistent storage of raw web pages)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Data Security & Tenant Isolation | `conversation_settings` scoped by `conversation_id` with RLS transitively enforcing project ownership, matching prior slices | PASS |
| II. Retrieval Accuracy & Source Fidelity | Web-search-augmented answers still carry citations distinguishing web sources from project-document sources; document-type filter changes only narrow, never fabricate, retrieval scope | PASS — extends FR-005/FR-006 from spec; citation model reused from 003-rag-project-chat |
| III. End-to-End Observability | Settings changes and their effective values for a given answer should be attributable (e.g., which settings were in effect) for debugging/audit, consistent with existing status/citation persistence patterns | PASS — settings snapshot recorded per generated message (see data-model) |
| IV. Code Quality & Type Safety | Backend Python + FastAPI + Pydantic settings schema; frontend TypeScript; unit + integration tests required before task completion | PASS |
| V. Performance & Asynchronous Processing | Settings read is a fast, single-row Postgres lookup added to the existing async `ask` flow; web-search routing node runs within the existing async LangGraph execution, not blocking | PASS |
| VI. Consistent UX & Design System | Panel built from existing glass-panel components and theme provider; collapsible right-hand placement is additive, not a new design language | PASS |
| VII. Graceful Failure & Error Transparency | In-flight generation uses the settings captured at question-submission time (FR-013); if the web-search step fails/times out, the flow must gracefully fall back to document-only retrieval rather than failing the whole answer | PASS — explicit fallback behavior specified in research.md |
| VIII. Enterprise Readiness | Settings changes and effective-settings-per-answer are auditable; least-privilege RLS on the new table | PASS |

No violations requiring Complexity Tracking justification.

## Project Structure

### Documentation (this feature)

```text
specs/004-rag-settings-panel/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/
│   │   └── routes/
│   │       └── conversation_settings.py   # GET/PATCH settings endpoints
│   ├── rag/
│   │   ├── retriever.py             # (existing, 003) now parameterized by retrieval_top_k + document-type filter
│   │   ├── web_search.py            # web search client + routing node (new)
│   │   ├── generation.py            # (existing, 003) now parameterized by temperature
│   │   └── graph.py                 # (extended) conditional web-search routing edge before generation
│   ├── models/                      # + ConversationSettings Pydantic schema
│   ├── services/                    # + settings read/upsert service, effective-settings snapshot helper
│   └── db/
├── migrations/                      # conversation_settings table + RLS
└── tests/
    ├── contract/                    # settings GET/PATCH contract tests
    ├── integration/                 # settings-applied-to-next-question, in-flight-unaffected, web-search-fallback, document-type-filter tests
    └── unit/                        # routing-node decision logic, settings validation (e.g., reject empty document-type set)

frontend/
├── app/(app)/projects/[projectId]/chat/[threadId]/
│   └── page.tsx                      # (existing, 003) now renders the settings panel alongside chat
├── components/
│   └── settings-panel/               # collapsible right-hand GlassPanel, web-search toggle, creativity control, chunk-count control, document-type checklist
├── lib/
│   └── settings/                     # client hook: local optimistic state + immediate persistence to backend on change
└── tests/
    ├── unit/
    └── e2e/                          # Playwright: open panel, toggle web search, adjust creativity/top-k, filter document types, reload-persistence, no-page-reload verification
```

**Structure Decision**: Extends `backend/app/rag/` (from 003-rag-project-chat) with a new
`web_search.py` node and parameterizes the existing retriever/generation modules rather than
duplicating them, keeping the LangGraph graph definition as the single place stage ordering is
expressed (Principle IV). The frontend adds a self-contained `components/settings-panel/`
directory built entirely from existing design-system primitives, plus a small `lib/settings/`
client hook mirroring the optimistic-update pattern already used for chat state.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations — table intentionally left without entries.

