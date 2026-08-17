# Implementation Plan: Document Processing Pipeline

**Branch**: `002-document-processing-pipeline` | **Date**: 2026-08-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-document-processing-pipeline/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

Implement the document ingestion and processing pipeline as an explicit LangGraph state
machine whose node states map 1:1 to the visible statuses (uploaded, queued, partitioning,
chunking, summarizing, vectorizing, stored, failed). Documents are partitioned into typed
elements using the Unstructured library and chunked by title to preserve document structure.
Table/image elements are summarized via Gemini's multimodal capability before embedding, with
a persisted reference back to the original asset in Supabase Storage. Image-only/scanned
documents run an explicit OCR step before partitioning. Every final chunk is represented as a
LangChain `Document` (page_content = raw text or summary; metadata = source document id,
element type, asset reference, page number, processing timestamp) and embedded into pgvector
alongside that metadata. Per-document element counts and per-element metadata are persisted in
Supabase Postgres so status-detail views can be queried directly. Processing status is
streamed to the frontend over SSE/WebSocket so the UI updates live without polling, and status
is fully recoverable from persisted state on reload.

## Technical Context

**Language/Version**: Python 3.11+ (backend/pipeline), TypeScript 5.x (frontend, Next.js
App Router — reused from 001-core-foundation)

**Primary Dependencies**: FastAPI, Pydantic v2, LangGraph (pipeline state machine), LangChain
(`Document` schema, pgvector integration), `unstructured` library (partitioning + chunk-by-title),
an OCR engine invoked as an explicit pre-partitioning step for image-only/scanned documents
(e.g., Unstructured's built-in OCR strategy or a dedicated OCR dependency such as Tesseract),
Google Gemini API client (multimodal table/image summarization), Supabase Python client
(Postgres + Storage), `pgvector` Postgres extension, an async task/worker mechanism (e.g.,
FastAPI `BackgroundTasks` or a dedicated queue/worker such as Celery/RQ/Arq — selected in
research.md) for async pipeline execution, SSE (`sse-starlette` or native `StreamingResponse`)
or WebSocket for live status delivery

**Storage**: Supabase Postgres (documents, processing_status_events, elements, chunks tables)
with `pgvector` extension for chunk embeddings; Supabase Storage for original document files
and extracted table/image assets

**Testing**: `pytest` for pipeline unit tests (per LangGraph node), integration tests
(end-to-end document → stored, including OCR and summarization paths, using fixture
documents), and RLS/isolation tests (cross-project chunk/element access denial); Vitest/Jest +
Playwright on the frontend for live-status UI and reload-recovery scenarios

**Target Platform**: Same web application as 001-core-foundation; pipeline execution runs
server-side (backend process/worker), not in the browser

**Project Type**: Web application (frontend + backend) — extends the `backend/` and
`frontend/` structure established in 001-core-foundation

**Performance Goals**: Status change reflected in UI within 3s of the underlying stage
transition (SC-002); upload call returns control to the user in <2s regardless of total
processing time (SC-007); document detail view (element counts/metadata) loads in <1s with
zero re-processing (SC-005)

**Constraints**: Processing MUST be fully asynchronous and MUST NOT block the UI or other
documents' processing (constitution Principle V; FR-006, FR-022); every element/chunk/summary
MUST be scoped and isolated per-project consistent with 001-core-foundation's RLS model
(constitution Principle I; FR-019–FR-021); every chunk MUST carry complete source-traceability
metadata (constitution Principle II; FR-014–FR-015); every stage MUST be independently
observable with persisted, queryable status (constitution Principle III; FR-003–FR-005,
FR-008); failures MUST be explicit, classified, and never silent (constitution Principle VII;
FR-005, FR-013)

**Scale/Scope**: Handles documents of varying size/complexity (multi-page, multiple
tables/images) per project, with multiple documents processing concurrently and
independently across multiple projects/users; this slice covers ingestion through
vectorized/stored chunks only — the retrieval/answer-generation (query-time RAG) experience
is a separate future slice

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Data Security & Tenant Isolation | Every document/element/chunk/embedding row scoped by `project_id`; RLS enforced on all new tables; Supabase Storage paths namespaced per project; no cross-project joins | PASS — extends 001-core-foundation's RLS pattern to `documents`, `elements`, `chunks`, `processing_status_events` |
| II. Retrieval Accuracy & Source Fidelity | Chunk-by-title preserves structural context; every chunk carries source document, element type, page, asset reference, and timestamp metadata; summaries only replace raw content for non-text elements (tables/images), never silently altering text content | PASS — directly implements FR-009, FR-014, FR-015 |
| III. End-to-End Observability | LangGraph states map exactly to the 8 visible statuses; every transition persisted as a `processing_status_events` row with timestamp and (on failure) reason; SSE/WebSocket streams live updates; status fully reconstructable from persisted state on reload | PASS — directly implements FR-003–FR-005, FR-007, FR-008, FR-023 |
| IV. Code Quality & Type Safety | Backend Python + FastAPI + Pydantic (matches constraint); LangChain `Document`/LangGraph state typed via Pydantic models; unit + integration tests required per pipeline stage before task completion | PASS |
| V. Performance & Asynchronous Processing | Pipeline runs as background async work triggered by upload, never inline in the request/response cycle; large/slow documents do not block other documents or the UI | PASS — directly implements FR-006, FR-022, SC-007 |
| VI. Consistent UX & Design System | Status UI (progress indicators, failure states, detail drill-down) reuses the Liquid Glass design system and light/dark theme provider from 001-core-foundation — no new ad hoc styling | PASS |
| VII. Graceful Failure & Error Transparency | Explicit `failed` state from any stage with human-readable reason; summarization transient failures retried before marking failed; OCR-no-usable-text case explicitly handled; partial failures do not leave documents in ambiguous intermediate states | PASS — directly implements FR-004, FR-005, FR-013, edge cases |
| VIII. Enterprise Readiness | Persisted audit trail of every status transition; least-privilege RLS on new tables/storage; production-capable design (no experimental shortcuts) for core pipeline | PASS |

No violations requiring Complexity Tracking justification. One deferred technical decision
(async execution mechanism: `BackgroundTasks` vs. dedicated queue/worker) is resolved in
Phase 0 research rather than treated as a constitution gate issue.

## Project Structure

### Documentation (this feature)

```text
specs/002-document-processing-pipeline/
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
│   │       ├── documents.py       # upload endpoint, document list/detail endpoints
│   │       └── status_stream.py   # SSE/WebSocket endpoint for live processing status
│   ├── pipeline/
│   │   ├── graph.py               # LangGraph state machine definition (8 states)
│   │   ├── nodes/
│   │   │   ├── ocr.py             # explicit OCR step for image-only/scanned docs
│   │   │   ├── partition.py       # Unstructured partitioning into typed elements
│   │   │   ├── chunk.py           # chunk-by-title
│   │   │   ├── summarize.py       # Gemini multimodal summarization for tables/images
│   │   │   └── vectorize.py       # embedding + pgvector storage
│   │   └── status_events.py       # persists processing_status_events, publishes to stream
│   ├── models/                     # Pydantic schemas: Document, Element, Chunk, AssetReference, Summary, StatusEvent
│   ├── services/                   # document upload handling, status query service, detail-view service
│   ├── db/                         # Supabase/Postgres + pgvector client helpers, Storage client
│   └── main.py
├── migrations/                     # documents, processing_status_events, elements, chunks tables + RLS + pgvector extension
└── tests/
    ├── contract/                  # upload/list/detail/status-stream API contract tests
    ├── integration/               # end-to-end pipeline tests (text doc, table/image doc, scanned doc, failure cases), cross-project isolation tests
    └── unit/                      # per-node LangGraph unit tests

frontend/
├── app/(app)/projects/[projectId]/
│   └── documents/
│       ├── page.tsx                # document list with live status indicators
│       └── [documentId]/
│           └── page.tsx            # document detail / element drill-down view
├── components/
│   └── documents/                  # status badge, progress stepper, element/table/image detail components (built on design-system primitives)
├── lib/
│   └── status/                     # SSE/WebSocket client hook for live status updates + reload-recovery fetch
└── tests/
    ├── unit/
    └── e2e/                        # Playwright: upload+watch, reload-mid-processing, drill-down, scanned-doc OCR, cross-project isolation UI checks
```

**Structure Decision**: Extends the existing `backend/` + `frontend/` layout from
001-core-foundation. The pipeline lives in a new `backend/app/pipeline/` module (LangGraph
graph + one node per processing stage) kept separate from `api/` and `services/` to isolate
processing logic from request handling, matching Principle IV's modularity expectation. The
frontend adds a `documents/` route segment nested under the existing per-project layout, and a
dedicated `lib/status/` client for the streaming connection, reusing the design-system and
theme provider already established in 001-core-foundation rather than introducing new styling.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations — table intentionally left without entries.

