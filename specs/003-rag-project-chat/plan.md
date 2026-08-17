# Implementation Plan: RAG Project Chat

**Branch**: `003-rag-project-chat` | **Date**: 2026-08-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-rag-project-chat/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

Implement project-scoped RAG chat using LangChain: embed the user's question, run a
similarity search restricted to the active project's rows in pgvector, and assemble the
retrieved LangChain `Document`s (their `page_content` + metadata from
002-document-processing-pipeline) into context sent to Gemini for answer generation. When a
retrieved chunk that contributed to the answer originated from a table/image summary, its
metadata's asset reference is used to attach the original table/image to the response
(FR-006–FR-008). Generated responses stream to the frontend over SSE, with distinct
"retrieving" and "generating" phases surfaced live. Chat messages, their generation status,
and the specific source chunks that backed each answer are persisted in Supabase Postgres,
scoped by project and conversation thread, with RLS consistent with 001-core-foundation and
002-document-processing-pipeline.

## Technical Context

**Language/Version**: Python 3.11+ (backend/retrieval+generation), TypeScript 5.x (frontend,
Next.js App Router — reused from prior slices)

**Primary Dependencies**: FastAPI, Pydantic v2, LangChain (embeddings interface, vector store
retriever over pgvector, `Document` assembly), Google Gemini API client (chat/generation,
reusing the multimodal client already integrated in 002-document-processing-pipeline),
Supabase Python client (Postgres + Storage for asset URLs), `pgvector` (already provisioned),
SSE (`sse-starlette` / `StreamingResponse`, consistent with the status-stream pattern from
002-document-processing-pipeline) for token/answer streaming

**Storage**: Supabase Postgres — new `messages` and `message_citations` tables (this feature),
reusing existing `conversations` (001-core-foundation) and `chunks`/`elements`/
`asset_references` (002-document-processing-pipeline) tables as read-only retrieval sources

**Testing**: `pytest` for retrieval unit tests (similarity search scoping, citation assembly),
integration tests (end-to-end ask → grounded answer with citations, insufficient-evidence
case, table/image attachment case), RLS/isolation tests for new tables; Vitest/Jest +
Playwright for streaming UI states (retrieving/generating), multi-thread switching, and
concurrent-message handling

**Target Platform**: Same web application as prior slices; retrieval + generation run
server-side (FastAPI request handler streaming via SSE), not client-side

**Project Type**: Web application (frontend + backend) — extends `backend/` and `frontend/`
from 001-core-foundation and 002-document-processing-pipeline

**Performance Goals**: "Retrieving" indicator shown within 1s of question submission;
"generating" indicator shown once retrieval completes (SC-004); thread switch loads correct
history in <2s (SC-006); app remains fully responsive during 100% of in-progress generations
(SC-007)

**Constraints**: Retrieval MUST be strictly scoped to the active project's stored chunks only
— no cross-project leakage (constitution Principle I; FR-013); every answer MUST carry a
verifiable citation or an explicit insufficient-evidence statement, never an unqualified claim
(constitution Principle II; FR-002–FR-005); answer generation MUST run asynchronously/streamed
and MUST NOT block other UI interactions (constitution Principle V; FR-015); a failed
generation MUST surface a clear per-message error without corrupting thread history
(constitution Principle VII; FR-016); concurrent messages within a thread MUST NOT be lost,
duplicated, or misordered (FR-018)

**Scale/Scope**: Multiple concurrent conversation threads per project, each independently
streaming; this slice covers question → retrieval → grounded generation → citation-backed,
persisted response — it does not cover document upload/processing (002) or project/auth
management (001), which it depends on as read-only/foundational context

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Data Security & Tenant Isolation | Similarity search query MUST filter pgvector rows by `project_id` before ranking; new `messages`/`message_citations` tables scoped by project + thread with RLS; no cross-project chunk ever enters the Gemini context | PASS — retriever built with a mandatory project-scoped filter, not an optional one |
| II. Retrieval Accuracy & Source Fidelity | Every answer's context is assembled only from retrieved LangChain `Document`s with real chunk metadata; citations reference the exact chunk/document/page; insufficient-evidence case explicitly handled rather than hallucinated | PASS — directly implements FR-002–FR-005, extends 002's traceability guarantee |
| III. End-to-End Observability | Message generation lifecycle (retrieving → generating → complete/failed) persisted and streamed, mirroring the status-event pattern from 002-document-processing-pipeline | PASS |
| IV. Code Quality & Type Safety | Backend Python + FastAPI + Pydantic; LangChain `Document`/message schemas typed via Pydantic; unit + integration tests required before task completion | PASS |
| V. Performance & Asynchronous Processing | Generation runs as an async streamed request, never blocking the main thread/UI; other navigation unaffected during generation (FR-015, FR-019) | PASS |
| VI. Consistent UX & Design System | Retrieving/generating indicators and citation/table/image display reuse the Liquid Glass design system and theme provider from 001-core-foundation; no new ad hoc styling | PASS |
| VII. Graceful Failure & Error Transparency | Generation failure/timeout surfaces a clear per-message error state without corrupting thread history (FR-016); insufficient-evidence is a distinct, explicit state, not a silent failure | PASS |
| VIII. Enterprise Readiness | Persisted audit trail of every message + its backing citations; least-privilege RLS on new tables; production-capable design | PASS |

No violations requiring Complexity Tracking justification.

## Project Structure

### Documentation (this feature)

```text
specs/003-rag-project-chat/
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
│   │       └── chat.py             # ask-question endpoint (SSE stream), thread create/list/history endpoints
│   ├── rag/
│   │   ├── retriever.py            # project-scoped pgvector similarity search via LangChain retriever
│   │   ├── context_assembly.py     # assembles retrieved Documents into Gemini prompt context
│   │   ├── generation.py           # Gemini call + SSE token/answer streaming, retrieving/generating phase events
│   │   └── citations.py            # maps contributing chunks -> citations, resolves table/image asset attachments
│   ├── models/                     # Pydantic schemas: Message, MessageCitation, RetrievalResult
│   ├── services/                   # message persistence, thread history service, concurrency-safe message ordering
│   ├── db/                         # (existing) Supabase/Postgres + pgvector client helpers
│   └── main.py
├── migrations/                     # messages, message_citations tables + RLS
└── tests/
    ├── contract/                   # ask/thread/history API contract tests, SSE event-shape tests
    ├── integration/                # end-to-end grounded-answer, insufficient-evidence, table/image attachment, cross-project isolation, concurrent-message tests
    └── unit/                       # retriever scoping, citation assembly, context assembly unit tests

frontend/
├── app/(app)/projects/[projectId]/chat/
│   ├── page.tsx                     # thread list + active thread chat view (extends 001-core-foundation's chat shell)
│   └── [threadId]/
│       └── page.tsx                 # thread-specific message history + composer
├── components/
│   └── chat/                        # message bubble, retrieving/generating indicator, citation chip, table/image attachment renderer (built on design-system primitives)
├── lib/
│   └── chat/                        # SSE client hook for streaming answers + phase events
└── tests/
    ├── unit/
    └── e2e/                         # Playwright: grounded answer + citation, table/image display, multi-thread switch, retrieving/generating states, concurrent messages, cross-project isolation
```

**Structure Decision**: Extends the existing `backend/` + `frontend/` layout. Retrieval and
generation logic live in a new `backend/app/rag/` module (separate from `pipeline/` in
002-document-processing-pipeline) since this is a query-time concern distinct from
ingestion-time processing, though both reuse the same `chunks`/`elements`/`asset_references`
tables as their shared data foundation. The frontend nests thread-specific chat routes under
the project chat shell already established in 001-core-foundation, and adds a `lib/chat/` SSE
client analogous to the `lib/status/` client from 002-document-processing-pipeline.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations — table intentionally left without entries.

