# Quickstart: Document Processing Pipeline

This guide validates the document processing pipeline end-to-end: upload, live status,
reload recovery, structural chunking, table/image summarization, OCR, and isolation.

## Prerequisites

- 001-core-foundation deployed and working (auth, project creation, RLS baseline).
- Supabase Postgres migrated with `documents`, `processing_status_events`, `elements`,
  `asset_references`, `summaries`, `chunks` tables (see [data-model.md](./data-model.md)),
  `pgvector` extension enabled, and RLS policies applied.
- Supabase Storage bucket configured for original documents and extracted table/image assets,
  namespaced by `project_id`.
- Backend `.env` configured with a Gemini API key (never exposed to the frontend) and queue/
  worker connection details for background pipeline execution.
- Background worker process running alongside the FastAPI app (see research.md decision on
  async execution mechanism).
- Test fixture documents: (a) a plain text/PDF document, (b) a document containing at least
  one table and one image, (c) a scanned/image-only PDF, (d) an unsupported file type, (e) a
  corrupted/empty file.

## Setup

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload &
python -m app.pipeline.worker   # or the chosen queue worker entrypoint

# Frontend
cd frontend
npm install
npm run dev
```

## Validation Scenarios

### 1. Upload and watch live status (User Story 1)

1. Open a project and upload fixture (a).
2. Confirm the document appears immediately with status `uploaded`, then `queued`, without
   any page refresh.
3. Watch the status advance through `partitioning → chunking → summarizing → vectorizing →
   stored` live via the SSE stream.
4. Open the same project in a second browser tab; confirm both tabs show the same live status
   progression simultaneously.

**Expected**: Status change visible within 3s of the underlying transition (SC-002); no manual
refresh needed at any point.

### 2. Reload mid-processing (User Story 2)

1. Upload a larger fixture document.
2. While it is at, e.g., the `chunking` stage, reload the browser page.
3. Confirm the document immediately displays `chunking` (its true current stage), not
   `uploaded` or blank, and that live updates resume.

**Expected**: Matches FR-008/FR-023; 100% status accuracy on reload (SC-001).

### 3. Drill into processing detail (User Story 3)

1. Wait for fixture (b) (table + image document) to reach `stored`.
2. Open its detail view; confirm total element count and breakdown by type are shown
   instantly (no re-processing delay).
3. Open the table/image element's detail; confirm the generated summary text is shown
   alongside a way to view the original asset.

**Expected**: Detail loads in <1s with 0 re-processing triggered (SC-005); FR-016–FR-018.

### 4. Scanned/image-only document via OCR (User Story 4)

1. Upload fixture (c) (scanned/image-only PDF).
2. Confirm the visible status includes an explicit OCR step before `partitioning`.
3. Confirm the document proceeds normally to `stored` once OCR succeeds.
4. Separately, upload a fixture with no genuinely readable content and confirm it reaches
   `failed` with a reason indicating no readable content was found (FR-013).

**Expected**: Matches FR-012/FR-013; ≥95% success rate for genuinely readable scanned content
(SC-008).

### 5. Source traceability (User Story 5)

1. For any stored document, fetch its chunks (e.g., via the elements endpoint or a direct
   database check in a test environment).
2. Confirm every chunk includes `document_id`, `element_type`, `page_number` (where
   applicable), and `processed_at`.
3. For a chunk derived from a table/image, confirm it also includes a valid
   `asset_reference_id`.

**Expected**: 100% of sampled chunks contain complete traceability metadata (SC-006).

### 6. Non-blocking uploads (User Story 6)

1. Upload a large/slow document.
2. Immediately (without waiting) navigate to a different project or perform another action.
3. Confirm no freeze, blocking spinner, or forced wait is tied to the uploading document's
   processing.

**Expected**: Upload call returns in <2s (SC-007); navigation is unaffected by ongoing
processing.

### 7. Rejection of unsupported files and failure handling

1. Attempt to upload fixture (d) (unsupported file type). Confirm it is rejected at upload
   time with a specific reason (FR-002), never entering the pipeline.
2. Upload fixture (e) (corrupted/empty file). Confirm it reaches `failed` with a clear reason
   rather than being stuck in an intermediate stage.

**Expected**: Matches FR-002, FR-005; SC-004 (100% of failures have a clear reason).

### 8. Cross-project / cross-user isolation

1. Using two different projects (and, separately, two different users), upload documents to
   each.
2. Attempt to fetch project A's document detail, elements, and status stream using project
   B's/another user's session.
3. Confirm every such request returns `404 Not Found` and no data from project A ever appears
   in project B's document list, detail view, or status stream.

**Expected**: 0 instances of cross-project/cross-user data exposure (SC-003).

## Automated Test Coverage (see plan.md Project Structure)

- `backend/tests/unit/` — one test module per LangGraph node (ocr, partition, chunk,
  summarize, vectorize), including failure/retry paths.
- `backend/tests/integration/` — full pipeline runs against fixture documents (a)–(e); RLS
  isolation tests across projects/users for all six new tables and Storage paths.
- `backend/tests/contract/` — request/response contract tests per [contracts/api.md](./contracts/api.md),
  including the SSE stream's reconnect/initial-snapshot behavior.
- `frontend/tests/e2e/` — Playwright flows mirroring scenarios 1–8 above.
