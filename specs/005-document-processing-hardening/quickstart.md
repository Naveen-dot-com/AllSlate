# Quickstart: Document Processing Hardening

This guide validates hardened processing behavior: confidence marking, document-level
partial/uncertain rollup, explicit failure routing, and reprocessing determinism.

## Prerequisites

- 002-document-processing-pipeline deployed and working.
- Backend migrated with the `elements.confidence`/`confidence_reason` and
  `documents.failure_category` columns (see [data-model.md](./data-model.md)); `documents.status`
  CHECK constraint updated to allow `stored_partial`.
- Hardening fixture documents present in `backend/tests/fixtures/hardening/` (see
  [research.md](./research.md) #7): scanned-readable PDF, scanned-illegible-page PDF,
  multi-language PDF, dense/irregular-table PDF, poor-quality-scan PDF.

## Setup

```bash
cd backend
uvicorn app.main:app --reload &
python -m app.pipeline.worker
```

## Validation Scenarios

### 1. Every supported document reaches a usable outcome (User Story 1)

1. Upload the scanned-readable PDF fixture; confirm it reaches `stored` with text content that
   matches the fixture's known content.
2. Upload the scanned-illegible-page PDF fixture; confirm the affected page(s) are marked
   `uncertain`/failed appropriately and the overall document status reflects that (either
   `stored_partial` if the rest is usable, or `failed` if not — per the configured threshold).
3. Upload the dense/irregular-table PDF fixture; confirm it reaches `stored` or `stored_partial`
   with the table element correctly extracted or explicitly marked uncertain.
4. Upload the multi-language PDF fixture; confirm supported-language content is processed
   normally and the unsupported-language segment is flagged, not silently dropped or causing
   full failure.
5. Upload the poor-quality-scan PDF fixture; confirm a best-effort result — either `stored`/
   `stored_partial` with usable content, or `failed` with a scan-quality-specific reason.

**Expected**: 0 documents left stuck or silently degraded (SC-001); 0 `stored` documents with
unusable content (SC-002).

### 2. Inspection views reflect actual confidence (User Story 2)

1. For the scanned-illegible-page fixture (assuming it reaches `stored_partial`), open its
   element detail view; confirm the illegible page's element(s) show a clear low-confidence/
   uncertain indicator distinct from confidently-extracted elements.
2. For the dense/irregular-table fixture, if the table was extracted with low confidence,
   confirm its detail view shows an uncertainty indicator rather than presenting it as a
   clean, confident extraction.
3. Open the overall document detail for any `stored_partial` document; confirm a document-level
   partial/uncertain indicator is shown.
4. Open the document detail for the fully successful scanned-readable fixture; confirm no
   partial/uncertain indicators appear anywhere in it.

**Expected**: 100% of partial/uncertain elements visibly marked (SC-003); 100% of
`stored_partial` documents show the document-level indicator with 0 false negatives (SC-004).

### 3. Specific, distinguishable failure reasons (User Story 3)

1. Upload a fixture designed to fail due to illegible scan quality; confirm the failure
   category is `illegible_scan` (or equivalent) with a specific reason text.
2. Upload a fixture designed to fail due to an unprocessable language; confirm the failure
   category is `unsupported_language` with a specific reason.
3. Upload a fixture designed to fail due to severely malformed table structure; confirm the
   failure category is `malformed_table` with a specific reason.
4. Compare the three failure reasons; confirm they are clearly distinguishable from one
   another, not identical generic text.

**Expected**: At least 90% of hardening-category failure reasons judged specific/actionable in
review (SC-005).

### 4. Reprocessing determinism

1. Reprocess the poor-quality-scan fixture (or any borderline-confidence fixture) three times
   under unchanged configuration.
2. Confirm the final status and (if applicable) failure category/category bucket are
   identical across all three runs.

**Expected**: 100% consistent outcomes across repeated runs (SC-006).

### 5. No unhandled exceptions on partition/OCR failure

1. Trigger a partition/OCR-level exception (e.g., via a corrupted or deliberately
   malformed fixture).
2. Confirm the worker does not crash; the document instead reaches `failed` status with a
   specific reason via the explicit LangGraph error edge.

**Expected**: Matches FR-001/FR-004/FR-014; 0 unhandled worker crashes observed.

## Automated Test Coverage (see plan.md Project Structure)

- `backend/tests/fixtures/hardening/` — the five hardening documents described above.
- `backend/tests/unit/` — confidence computation bucketing, error-edge routing,
  failure-category mapping specificity.
- `backend/tests/integration/` — full-pipeline runs per hardening fixture asserting final
  status, confidence markers, and failure category; reprocessing-determinism test (run each
  fixture 3x, assert identical outcome).
- `frontend/tests/e2e/` — verifies confidence badges and document-level partial indicators
  render correctly for `stored_partial` documents.
