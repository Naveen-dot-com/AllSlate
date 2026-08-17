# Tasks: Document Processing Pipeline

**Input**: Design documents from `/specs/002-document-processing-pipeline/`

**Prerequisites**: plan.md, spec.md, data-model.md, contracts/, research.md

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize the backend/frontend structure and shared tooling needed for the pipeline.

- [X] T001 [P] Create the backend pipeline module structure in backend/app/pipeline/, backend/app/models/, backend/app/services/, and backend/app/db/
- [X] T002 [P] Add Python dependencies for FastAPI, Pydantic v2, LangGraph, LangChain, Unstructured, Supabase client, pgvector, pytest, and SSE support in backend/requirements.txt or pyproject.toml
- [ ] T003 [P] Add frontend document status dependencies and route scaffolding in frontend/app/(app)/projects/[projectId]/documents/, frontend/components/documents/, and frontend/lib/status/
- [ ] T004 Configure linting and formatting for the Python backend and TypeScript frontend in backend/pyproject.toml and frontend/package.json

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the shared persistence, auth boundaries, and pipeline skeleton that all stories rely on.

**Checkpoint**: Once this phase is complete, user-story implementation may begin in parallel.

- [ ] T005 Create the Supabase/Postgres migration for documents, processing_status_events, elements, asset_references, summaries, and chunks with pgvector, indexes, and RLS in backend/migrations/
- [X] T006 [P] Implement project-scoped ownership and auth dependencies for all document APIs in backend/app/api/dependencies.py and backend/app/api/routes/
- [X] T007 [P] Define shared Pydantic models for documents, status events, elements, summaries, asset references, and chunks in backend/app/models/
- [X] T008 Implement the LangGraph processing graph skeleton and status-state model in backend/app/pipeline/graph.py
- [X] T009 Implement the shared status-event publisher and persisted stage transition utility in backend/app/pipeline/status_events.py
- [X] T010 Build the upload validation, storage path naming, and document service helpers in backend/app/services/document_upload.py and backend/app/db/storage.py

---

## Phase 3: User Story 1 - Upload a Document and Watch It Process (Priority: P1) 🎯 MVP

**Goal**: Accept uploads, process asynchronously, emit live status changes, and reach the stored state without blocking the app.

**Independent Test**: Upload one document to a project and verify the visible status advances through uploaded → queued → partitioning → chunking → summarizing → vectorizing → stored (or failed with a reason) without manually refreshing.

### Tests for User Story 1

- [X] T011 [P] [US1] Contract test for POST /api/v1/projects/{project_id}/documents in backend/tests/contract/test_documents_upload.py
- [X] T012 [P] [US1] Integration test for the full async processing flow in backend/tests/integration/test_document_pipeline.py
- [ ] T013 [P] [US1] Frontend live-status UI test in frontend/tests/e2e/test_document_status_live.spec.ts

### Implementation for User Story 1

- [X] T014 [P] [US1] Implement the upload route, multipart handling, and 202/422/404 response contract in backend/app/api/routes/documents.py
- [X] T015 [US1] Implement async document ingestion and queueing behavior so uploads return immediately while processing continues in backend/app/services/document_ingest.py
- [X] T016 [US1] Wire the state machine to emit queued, partitioning, chunking, summarizing, vectorizing, stored, and failed transitions in backend/app/pipeline/graph.py
- [X] T017 [US1] Implement the partitioning node using Unstructured element extraction and structural metadata in backend/app/pipeline/nodes/partition.py
- [X] T018 [US1] Implement chunk creation by title/section while preserving page, element type, and document traceability in backend/app/pipeline/nodes/chunk.py
- [X] T019 [US1] Implement vectorization and pgvector persistence for final chunks in backend/app/pipeline/nodes/vectorize.py
- [X] T020 [US1] Implement explicit error propagation and failure reasons for any unrecoverable stage in backend/app/pipeline/graph.py and backend/app/pipeline/status_events.py
- [ ] T021 [US1] Add the project document list and status indicator UI with live updates in frontend/app/(app)/projects/[projectId]/documents/page.tsx and frontend/components/documents/DocumentStatusBadge.tsx
- [ ] T022 [US1] Add the client-side SSE connection and live status subscription helper in frontend/lib/status/useProjectDocumentStatus.ts

**Checkpoint**: At this point, User Story 1 should be fully functional and independently testable.

---

## Phase 4: User Story 2 - Reload Mid-Processing and See Accurate Status (Priority: P1)

**Goal**: Recover the true current stage after refresh or reconnect without stale or default status values.

**Independent Test**: Upload a document, reload mid-flight, and confirm the displayed status matches the actual persisted stage.

### Tests for User Story 2

- [X] T023 [P] [US2] Contract test for current-status recovery and status-stream replay in backend/tests/contract/test_status_stream.py
- [ ] T024 [P] [US2] Frontend reload-recovery E2E test in frontend/tests/e2e/test_document_reload_recovery.spec.ts

### Implementation for User Story 2

- [X] T025 [P] [US2] Implement latest-status and current-stage query helpers backed by processing_status_events in backend/app/services/status_service.py
- [X] T026 [US2] Update the status-stream route to emit the true current state on connect and replay subsequent events in backend/app/api/routes/status_stream.py
- [ ] T027 [US2] Hydrate document status on client reload and reconnect so UI reflects persisted current state in frontend/lib/status/useProjectDocumentStatus.ts
- [ ] T028 [US2] Add document list refresh behavior for multi-document reload recovery in frontend/app/(app)/projects/[projectId]/documents/page.tsx

**Checkpoint**: At this point, User Stories 1 and 2 both work independently and recover correctly after reload.

---

## Phase 5: User Story 3 - Drill Into a Document's Processing Detail (Priority: P2)

**Goal**: Show persisted per-document element counts and metadata without re-processing.

**Independent Test**: Open a processed document detail view and confirm counts and metadata are returned instantly from stored rows.

### Tests for User Story 3

- [ ] T029 [P] [US3] Contract test for GET /api/v1/projects/{project_id}/documents/{document_id} and the element list endpoint in backend/tests/contract/test_document_detail.py
- [ ] T030 [P] [US3] Unit test covering element-count aggregation by type in backend/tests/unit/test_element_counts.py

### Implementation for User Story 3

- [ ] T031 [P] [US3] Add persisted element-count and summary queries in backend/app/services/document_detail_service.py
- [ ] T032 [US3] Add the document detail route returning element_count and element_counts_by_type in backend/app/api/routes/documents.py
- [ ] T033 [US3] Implement the elements list route returning per-element metadata and summary/asset references in backend/app/api/routes/documents.py
- [ ] T034 [US3] Build the document detail page and breakdown UI in frontend/app/(app)/projects/[projectId]/documents/[documentId]/page.tsx and frontend/components/documents/DocumentDetail.tsx
- [ ] T035 [US3] Add signed URL retrieval and asset preview support for table/image references in backend/app/api/routes/documents.py and frontend/components/documents/AssetPreview.tsx

**Checkpoint**: At this point, the document detail screen is queryable and non-destructive.

---

## Phase 6: User Story 4 - Scanned or Image-Only Documents Are Still Made Searchable (Priority: P2)

**Goal**: Run an explicit OCR path for scanned or image-only files before partitioning, and fail clearly when no readable text is recovered.

**Independent Test**: Upload a scanned document and confirm the visible pipeline includes OCR before partitioning and that the output is searchable only if usable text is recovered.

### Tests for User Story 4

- [ ] T036 [P] [US4] Integration test for OCR path and successful scanned-document processing in backend/tests/integration/test_ocr_pipeline.py
- [ ] T037 [P] [US4] Failure-case test for scanned documents with no usable text in backend/tests/integration/test_ocr_failure.py

### Implementation for User Story 4

- [ ] T038 [P] [US4] Add OCR node and image-only/scanned detection logic in backend/app/pipeline/nodes/ocr.py
- [ ] T039 [US4] Wire the OCR stage into the graph ordering and failure path in backend/app/pipeline/graph.py
- [ ] T040 [US4] Add the explicit OCR stage to the frontend status flow and status badge display in frontend/components/documents/DocumentStatusBadge.tsx

**Checkpoint**: Scanned and image-only documents are treated as first-class pipeline inputs.

---

## Phase 7: User Story 5 - Every Answer Traces Back to Its Exact Source (Priority: P1)

**Goal**: Ensure each chunk records the exact source document, element type, page, and original asset reference.

**Independent Test**: Inspect a processed chunk and verify it includes the source document id, original element type, page number, processed time, and asset reference when applicable.

### Tests for User Story 5

- [ ] T041 [P] [US5] Unit test verifying chunk metadata for text and table/image-derived chunks in backend/tests/unit/test_chunk_metadata.py
- [ ] T042 [P] [US5] Contract test for asset-reference retrieval and source traceability in backend/tests/contract/test_chunk_traceability.py

### Implementation for User Story 5

- [ ] T043 [P] [US5] Update chunk and summary models to capture source traceability metadata and asset references in backend/app/models/chunks.py and backend/app/models/summaries.py
- [ ] T044 [US5] Implement source-aware chunk creation and asset reference persistence in backend/app/pipeline/nodes/chunk.py and backend/app/pipeline/nodes/summarize.py
- [ ] T045 [US5] Ensure vector store rows store the same provenance metadata as the persisted chunk rows in backend/app/pipeline/nodes/vectorize.py
- [ ] T046 [US5] Add the table/image asset preview and source trace UI in frontend/components/documents/AssetPreview.tsx and the document detail page

**Checkpoint**: Every chunk is independently traceable back to its source and asset.

---

## Phase 8: User Story 6 - Uploads Never Block the App (Priority: P3)

**Goal**: Keep the app responsive while uploads and processing run in the background across multiple documents.

**Independent Test**: Upload a large slow document and confirm the user can continue using the app without blocking or freezing while processing continues in the background.

### Tests for User Story 6

- [ ] T047 [P] [US6] Integration test for async uploads and background processing throughput in backend/tests/integration/test_background_processing.py
- [ ] T048 [P] [US6] Frontend E2E test confirming multi-document background uploads do not block navigation in frontend/tests/e2e/test_background_uploads.spec.ts

### Implementation for User Story 6

- [X] T049 [US6] Implement the asynchronous processing worker or task runner used after upload acceptance in backend/app/services/processing_service.py
- [X] T050 [US6] Ensure the upload endpoint returns immediately with 202 while background processing proceeds without blocking other app operations in backend/app/api/routes/documents.py
- [ ] T051 [US6] Add concurrency-safe project isolation and shared storage access checks for multiple uploads in backend/app/services/

**Checkpoint**: User Story 6 confirms the app remains responsive while documents continue processing in the background.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final quality, security, and validation pass across all stories.

- [ ] T052 [P] Run the full backend and frontend test matrix for document processing, status recovery, OCR, and project isolation in backend/tests/ and frontend/tests/
- [ ] T053 [P] Add or refine end-to-end quickstart validation and smoke coverage based on specs/002-document-processing-pipeline/quickstart.md
- [ ] T054 Review and harden cross-project access rules, storage scoping, and RLS enforcement for all new document pipeline tables in backend/migrations/
- [ ] T055 Update user-facing documentation for document upload, document status flow, OCR support, and source-traceability in docs/ or project README files
- [ ] T056 Final performance review of status-stream latency, upload response time, and detail-view query performance against the non-functional goals in plan.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; can begin immediately.
- **Foundational (Phase 2)**: Depends on setup completion and blocks all user story work.
- **User Stories (Phase 3–8)**: Each depends on the foundational phase and can proceed in parallel after foundation is complete.
- **Polish (Phase 9)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2; this is the primary MVP story.
- **US2 (P1)**: Can start after Phase 2 and should be validated alongside US1.
- **US3 (P2)**: Can start after the document pipeline is storing elements/chunks successfully.
- **US4 (P2)**: Can start after the core graph is established and OCR is integrated.
- **US5 (P1)**: Depends on chunk creation and summarization logic; can run in parallel with US3 once the shared pipeline is stable.
- **US6 (P3)**: Depends on the async processing contract; can run after US1 is working and is a final performance-quality validation.

### Within Each User Story

- Tests are written before implementation when feasible.
- Models and shared services are created before route or UI implementation.
- Status, tracing, and failure handling are validated before the story is considered complete.

---

## Parallel Opportunities

- All Setup tasks can proceed in parallel.
- Foundational tasks T005–T010 can be done in parallel if team capacity allows.
- All US1 tests marked [P] can run together.
- US2 tests and US3/US4/US5 tests can run in parallel once foundational work is complete.
- Model and service tasks within the same story are often parallelizable when they touch different files.
- The frontend status UI and backend pipeline work can proceed in parallel once the API contract and schema are established.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Implement User Story 1 end to end.
3. Validate status updates and final stored state without refresh.
4. Stop and confirm the baseline pipeline is reliable before continuing to US2–US6.

### Incremental Delivery

1. Setup + Foundation → shared contract and storage ready.
2. US1 → upload, live progress, async processing, stored state.
3. US2 → reload recovery and persisted status.
4. US3 → detail drill-down and element metadata.
5. US4 → OCR for scanned/image-only files.
6. US5 → source-traceability and asset references.
7. US6 → responsiveness and concurrency guarantees.
8. Polish → harden, optimize, and validate.

---

## Notes

- [P] tasks are only used for tasks touching different files or independent work streams.
- Every task includes a concrete file path so implementation can proceed without extra context.
- The tasks intentionally preserve story isolation so each user story can be validated independently.
- The backlog is aligned to the requirements in spec.md, plan.md, and the API/data-model contracts in this feature folder.
