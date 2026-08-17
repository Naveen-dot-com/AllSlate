# Implementation Plan: Document Processing Hardening

**Branch**: `005-document-processing-hardening` | **Date**: 2026-08-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/005-document-processing-hardening/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

Harden the 002-document-processing-pipeline LangGraph flow so difficult documents (scanned,
multi-language, dense/irregular tables, poor scan quality) always resolve to an accurate,
explicit outcome. Add OCR/extraction confidence tracking: every element (and, transitively,
each page/document) carries a confidence marker (`confident` / `partial` / `uncertain`) with a
human-readable reason, computed from the OCR engine's/Unstructured's own confidence signals
and table-structure regularity heuristics, and surfaced in the status-detail/inspection views
so uncertain content is never presented as ground truth. Add explicit error-handling edges in
the LangGraph pipeline so partition/OCR failures route deterministically to the existing
`failed` status (rather than an unhandled exception crashing the worker), with specific,
distinguishable failure reasons. Add a hardening-focused fixture test suite (scanned PDFs,
multi-language pages, complex tables, poor-quality scans) exercising these paths in
integration tests.

## Technical Context

**Language/Version**: Python 3.11+ (backend/pipeline — same stack as
002-document-processing-pipeline)

**Primary Dependencies**: Existing `unstructured` (partitioning/OCR), LangGraph (pipeline
graph, extended with explicit error-handling edges), Supabase Postgres (existing `elements`
table extended with confidence fields), no new external services required — this is a
hardening/reliability slice on top of the existing pipeline rather than a new capability

**Storage**: Supabase Postgres — extends `elements` (confidence fields) and `documents`
(document-level partial/uncertain rollup) from 002-document-processing-pipeline; no new
tables required

**Testing**: `pytest` — new hardening fixture suite (scanned PDF, multi-language PDF,
dense/irregular-table PDF, poor-quality-scan PDF, illegible/unreadable PDF, unsupported-
language-segment PDF) driving both unit tests (confidence computation, error-edge routing) and
integration tests (full pipeline run per fixture, asserting final status + confidence markers
+ failure reason specificity); existing 002 test suite extended, not replaced

**Target Platform**: Same backend pipeline execution environment as
002-document-processing-pipeline (worker process)

**Project Type**: Web application (backend-focused hardening; minor frontend changes to
surface confidence indicators) — extends `backend/` and `frontend/` from prior slices

**Performance Goals**: No new latency budget beyond existing pipeline performance goals from
002-document-processing-pipeline; confidence computation must not materially slow
partitioning/OCR (target: negligible added overhead, no explicit new SLA introduced)

**Constraints**: MUST NOT mark a document "stored" with empty/illegible/unusable content
(constitution Principle II, VII; FR-002); every partition/OCR failure MUST route to the
existing `failed` status via an explicit graph edge, never an unhandled exception
(constitution Principle VII; FR-004, FR-014); confidence markers MUST be visible in existing
inspection views without breaking their existing contract (constitution Principle III, VI;
FR-009, FR-010); reprocessing the same input MUST be deterministic (FR-016)

**Scale/Scope**: Applies to every document processed through the existing pipeline from
002-document-processing-pipeline; this slice modifies pipeline nodes and data model fields
rather than introducing new pipeline stages or new user-facing capabilities beyond
confidence/failure-reason visibility

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Data Security & Tenant Isolation | No new tables; extends existing project-scoped, RLS-protected `elements`/`documents` tables with additional columns only — isolation model unchanged | PASS |
| II. Retrieval Accuracy & Source Fidelity | Confidence markers directly prevent uncertain/illegible content from being presented as ground-truth fact; retrieval/citations (003-rag-project-chat) can reflect confidence per FR-015 | PASS — directly strengthens this principle |
| III. End-to-End Observability | Explicit LangGraph error edges make every partition/OCR failure an observable, logged `failed` status transition (reusing `processing_status_events` from 002) instead of a silent crash | PASS — directly implements FR-001, FR-014 |
| IV. Code Quality & Type Safety | Confidence fields added to existing Pydantic `Element`/`Document` models; new error-edge logic is unit-tested; hardening fixtures covered by pytest | PASS |
| V. Performance & Asynchronous Processing | Confidence computation reuses signals already produced by OCR/partitioning (no new heavy computation); error edges don't change the pipeline's async execution model | PASS |
| VI. Consistent UX & Design System | Low-confidence/partial indicators in the inspection view reuse existing design-system badge/indicator components, not new ad hoc styling | PASS |
| VII. Graceful Failure & Error Transparency | This entire slice is a direct implementation of this principle: explicit, specific, non-silent failure states for partition/OCR issues | PASS — primary purpose of this slice |
| VIII. Enterprise Readiness | Deterministic, reproducible outcomes (FR-016) and specific audit-friendly failure reasons strengthen enterprise reliability expectations | PASS |

No violations requiring Complexity Tracking justification.

## Project Structure

### Documentation (this feature)

```text
specs/005-document-processing-hardening/
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
│   ├── pipeline/
│   │   ├── graph.py                 # (extended, 002) explicit error edges from ocr/partition nodes to `failed`
│   │   ├── nodes/
│   │   │   ├── ocr.py               # (extended, 002) emits per-page confidence + reason
│   │   │   ├── partition.py         # (extended, 002) emits per-element confidence + table-structure regularity signal
│   │   │   └── errors.py            # (new) maps node-level exceptions/low-confidence-threshold breaches to specific failure reasons
│   │   └── status_events.py         # (existing, 002) now also records confidence-related failure reasons
│   ├── models/                      # + confidence fields on Element/Document Pydantic schemas
│   └── services/                    # detail-view service now surfaces confidence + document-level partial/uncertain rollup
├── migrations/                      # adds confidence columns to `elements`/`documents` (no new tables)
└── tests/
    ├── fixtures/
    │   └── hardening/                # (new) scanned PDF, multi-language PDF, dense/irregular-table PDF, poor-quality-scan PDF, illegible PDF
    ├── unit/                         # confidence computation, error-edge routing, failure-reason specificity
    └── integration/                  # full-pipeline runs per hardening fixture; reprocessing-determinism test

frontend/
├── components/
│   └── documents/                    # (extended, 002) element/chunk detail views add a low-confidence/partial badge
└── tests/
    └── e2e/                          # (extended) verifies confidence badges appear correctly for hardening fixtures
```

**Structure Decision**: This is a hardening slice, not a new subsystem — it modifies existing
002-document-processing-pipeline modules (`graph.py`, `ocr.py`, `partition.py`,
`status_events.py`, detail-view service) and existing `elements`/`documents` tables in place,
adding one new `errors.py` node-support module for centralized failure-reason mapping, plus a
new `tests/fixtures/hardening/` directory of difficult test documents. No new top-level
directories are introduced in either `backend/` or `frontend/`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations — table intentionally left without entries.

