# Tasks: Document Processing Hardening

**Input**: Design documents from `/specs/005-document-processing-hardening/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/api-changes.md](./contracts/api-changes.md), [quickstart.md](./quickstart.md)

**Tests**: Included — this hardening feature's scope explicitly requires new fixture-driven
tests, and the constitution (Principle IV) requires unit/integration tests before any task is
considered complete.

**Organization**: Tasks are grouped by user story (per spec.md) to enable independent
implementation and testing of each story. This feature extends existing
002-document-processing-pipeline modules in place; no new top-level directories beyond the
hardening fixtures and one new `errors.py` module.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Paths follow plan.md's Project Structure (`backend/app/...`, `frontend/...`)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare configuration and fixture scaffolding shared by all stories

- [X] T001 Create `backend/tests/fixtures/hardening/` directory and add fixture documents:
      scanned-readable PDF, scanned-illegible-page PDF, multi-language PDF (supported +
      unsupported language segment), dense/irregular-table PDF (merged cells, multi-page
      table), poor-quality-scan PDF
- [X] T002 [P] Add configuration values for OCR/table confidence thresholds and the
      partial-vs-fail document threshold in `backend/app/config.py` (or existing settings
      module), sourced from environment/config, not hardcoded inline
- [X] T003 [P] Document the supported-language set configuration used by OCR/partitioning in
      `backend/app/config.py`, consistent with research.md #5

**Checkpoint**: Fixtures and configuration scaffolding exist; ready for foundational schema work

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Data model and shared error-routing infrastructure that every user story depends on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Write migration adding `confidence` (`confident`/`partial`/`uncertain`, default
      `confident`) and `confidence_reason` (nullable) columns to `elements` in
      `backend/migrations/`
- [ ] T005 Write migration extending `documents.status` CHECK constraint to allow
      `stored_partial`, and adding nullable `failure_category` (CHECK IN `illegible_scan`,
      `unreadable_ocr_portion`, `malformed_table`, `unsupported_language`, `other`) in
      `backend/migrations/`
- [ ] T006 [P] Update the `Element` Pydantic model with `confidence`/`confidence_reason`
      fields in `backend/app/models/element.py`
- [ ] T007 [P] Update the `Document` Pydantic model with `stored_partial` status value and
      `failure_category` field in `backend/app/models/document.py`
- [X] T008 Implement confidence bucketing utility (raw OCR/table-regularity signal →
      `confident`/`partial`/`uncertain`, using the thresholds from T002) in
      `backend/app/pipeline/confidence.py`
- [X] T009 Implement `backend/app/pipeline/nodes/errors.py`: a shared mapping from
      partition/OCR node exceptions and confidence-threshold breaches to specific
      `failure_category` + human-readable `failure_reason` values (depends on T008)
- [X] T010 Implement document-level status rollup logic (all elements confident → `stored`;
      some partial/uncertain but within threshold → `stored_partial`; over threshold →
      `failed`) in `backend/app/services/document_status.py` (depends on T008)

**Checkpoint**: Schema and shared confidence/error-routing infrastructure ready — user story
implementation can now begin

---

## Phase 3: User Story 1 - Every Supported Document Reaches a Usable Outcome (Priority: P1) 🎯 MVP

**Goal**: Every hardened-category document (scanned, dense-table, multi-language,
poor-quality-scan) resolves to `stored`, `stored_partial`, or `failed` — never stuck, never
silently unusable.

**Independent Test**: Upload each hardening fixture and confirm it reaches a definitive,
correct outcome per quickstart.md Scenario 1.

### Tests for User Story 1 ⚠️

- [X] T011 [P] [US1] Integration test: scanned-readable fixture reaches `stored` with accurate
      content in `backend/tests/integration/test_hardening_scanned_readable.py`
- [X] T012 [P] [US1] Integration test: scanned-illegible-page fixture reaches
      `stored_partial` or `failed` per threshold, never silently `stored` with empty/garbled
      content, in `backend/tests/integration/test_hardening_scanned_illegible.py`
- [X] T013 [P] [US1] Integration test: dense/irregular-table fixture reaches `stored` or
      `stored_partial` with the table usably extracted or explicitly marked uncertain, in
      `backend/tests/integration/test_hardening_dense_table.py`
- [X] T014 [P] [US1] Integration test: multi-language fixture processes the supported-language
      portion normally and flags the unsupported segment without failing the whole document, in
      `backend/tests/integration/test_hardening_multilanguage.py`
- [X] T015 [P] [US1] Integration test: poor-quality-scan fixture produces a best-effort
      `stored`/`stored_partial` result or a scan-quality-specific `failed` reason, in
      `backend/tests/integration/test_hardening_poor_quality_scan.py`
- [X] T016 [P] [US1] Unit test: confidence bucketing utility (T008) correctly classifies
      sample confidence scores into `confident`/`partial`/`uncertain` in
      `backend/tests/unit/test_confidence.py`
- [X] T017 [P] [US1] Unit test: partial-vs-fail document rollup logic (T010) at and around the
      configured threshold in `backend/tests/unit/test_document_status.py`

### Implementation for User Story 1

- [ ] T018 [US1] Extend `backend/app/pipeline/nodes/ocr.py` to compute per-page confidence via
      the bucketing utility (T008) and attach `confidence`/`confidence_reason` to OCR output
      (depends on T008)
- [ ] T019 [US1] Extend `backend/app/pipeline/nodes/partition.py` to compute per-element
      confidence, including table-structure regularity checks for table elements, and persist
      `confidence`/`confidence_reason` on each `elements` row (depends on T006, T008)
- [ ] T020 [US1] Extend `backend/app/pipeline/nodes/partition.py` (or a dedicated language
      step) to detect unsupported-language segments per the configured language set (T003) and
      flag them via `confidence_reason = 'unsupported_language_segment'` rather than failing
      the whole document (depends on T019)
- [ ] T021 [US1] Add explicit conditional error edges from the `ocr` and `partition` nodes to
      the terminal `failed` node in `backend/app/pipeline/graph.py`, using the mapping from
      `errors.py` (T009) for exceptions and confidence-threshold breaches (depends on T009)
- [ ] T022 [US1] Wire document-level status rollup (T010) into the pipeline's final stage so a
      document's `status` (`stored`/`stored_partial`/`failed`) and `failure_category` are set
      correctly based on its elements' confidence (depends on T010, T018, T019)
- [ ] T023 [US1] Ensure `processing_status_events` records a status transition for
      `stored_partial` (not only `stored`/`failed`), consistent with the existing status-event
      pattern, in `backend/app/pipeline/status_events.py`

**Checkpoint**: Every hardening fixture reaches a correct, non-stuck, non-silently-unusable
outcome — User Story 1 independently testable and functional

---

## Phase 4: User Story 2 - Inspection Views Accurately Reflect What Was Extracted (Priority: P1)

**Goal**: Element/document detail views visibly distinguish confident, partial, and uncertain
extraction — never presenting uncertain content as ground truth.

**Independent Test**: Process a document with a known partial section and confirm its detail
view marks that section distinctly, per quickstart.md Scenario 2.

### Tests for User Story 2 ⚠️

- [ ] T024 [P] [US2] Contract test: `GET .../documents/{document_id}` response includes
      `status` (allowing `stored_partial`), `failure_category`, and
      `has_low_confidence_content` in `backend/tests/contract/test_document_detail.py`
- [ ] T025 [P] [US2] Contract test: `GET .../documents/{document_id}/elements` response
      includes `confidence`/`confidence_reason` per element in
      `backend/tests/contract/test_document_elements.py`
- [ ] T026 [P] [US2] Integration test: a document with mixed confident/partial elements shows
      correct per-element markers and a correct document-level rollup indicator, in
      `backend/tests/integration/test_hardening_inspection_view.py`
- [ ] T027 [P] [US2] Integration test: a fully confident document shows no partial/uncertain
      indicators anywhere (no false positives), in
      `backend/tests/integration/test_hardening_no_false_positives.py`

### Implementation for User Story 2

- [ ] T028 [US2] Update the document detail service to compute and return
      `has_low_confidence_content` and `failure_category` in
      `backend/app/services/document_status.py` (depends on T007, T010)
- [ ] T029 [US2] Update the document detail API route to serialize the extended fields in
      `backend/app/api/routes/documents.py` (depends on T028)
- [ ] T030 [US2] Update the elements list API route to serialize
      `confidence`/`confidence_reason` per element in
      `backend/app/api/routes/documents.py` (depends on T006)
- [ ] T031 [P] [US2] Add a low-confidence/partial badge component (using existing design-system
      primitives) in `frontend/components/documents/confidence-badge.tsx`
- [ ] T032 [US2] Wire the confidence badge into the element/chunk detail view and a
      document-level partial/uncertain indicator into the document detail view in
      `frontend/app/(app)/projects/[projectId]/documents/[documentId]/page.tsx` (depends on
      T031)
- [ ] T033 [P] [US2] Playwright e2e test verifying confidence badges render correctly for the
      hardening fixtures in `frontend/tests/e2e/hardening-confidence-badges.spec.ts`

**Checkpoint**: Inspection views correctly and visibly reflect actual extraction confidence —
User Stories 1 and 2 both independently functional

---

## Phase 5: User Story 3 - Clear, Specific Failure Reasons (Priority: P2)

**Goal**: Every failure produced by hardening logic is specific and distinguishable from other
failure reasons.

**Independent Test**: Trigger three different hardening failure categories and confirm
distinguishable reasons, per quickstart.md Scenario 3.

### Tests for User Story 3 ⚠️

- [ ] T034 [P] [US3] Unit test: `errors.py` mapping (T009) produces distinct
      `failure_category`/`failure_reason` pairs for illegible-scan, unreadable-OCR-portion,
      malformed-table, and unsupported-language causes, in
      `backend/tests/unit/test_error_mapping.py`
- [ ] T035 [P] [US3] Integration test: three fixtures designed to fail for three different
      reasons produce three distinguishable `failure_category`/`failure_reason` values, in
      `backend/tests/integration/test_hardening_failure_specificity.py`

### Implementation for User Story 3

- [ ] T036 [US3] Refine `backend/app/pipeline/nodes/errors.py` reason templates to reference
      the specific page/section/table/language at fault (e.g., "scanned pages 4–7 were
      unreadable") rather than generic text (depends on T009)
- [ ] T037 [US3] Ensure `failure_reason` and `failure_category` are both persisted together on
      every hardening-triggered failure in `backend/app/pipeline/status_events.py` (depends on
      T036)

**Checkpoint**: All three user stories independently functional and testable

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Reliability guarantees and final validation spanning all stories

- [ ] T038 [P] Integration test: reprocessing the same hardening fixture 3x under unchanged
      configuration yields identical status/failure-category outcomes each time, in
      `backend/tests/integration/test_hardening_determinism.py`
- [ ] T039 [P] Integration test: a deliberately malformed/corrupted fixture triggers a
      partition/OCR exception that is caught by the explicit error edges (T021) and resolves
      to `failed`, with 0 unhandled worker crashes, in
      `backend/tests/integration/test_hardening_no_unhandled_exception.py`
- [ ] T040 Ensure retrieval/citation code in `backend/app/rag/citations.py`
      (003-rag-project-chat) can read `elements.confidence`/`confidence_reason` via the
      existing `chunks.element_id` relationship, for future use surfacing confidence on chat
      citations (FR-015) — read-only wiring, no new schema
- [ ] T041 Run [quickstart.md](./quickstart.md) end-to-end validation across all 5 scenarios
      and confirm all success criteria (SC-001–SC-006) are met

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational — no dependency on US2/US3
- **User Story 2 (Phase 4)**: Depends on Foundational; reads data produced by US1's pipeline
  changes (T018–T022) to have meaningful confidence data, but its API/UI work can be
  scaffolded in parallel and only requires US1 for full end-to-end testing
- **User Story 3 (Phase 5)**: Depends on Foundational and on `errors.py` (T009) from
  Foundational; refines behavior introduced in US1 (T021) but is independently testable via
  unit tests on the mapping itself
- **Polish (Phase 6)**: Depends on US1–US3 being complete

### Within Each User Story

- Tests written first, expected to fail before implementation
- Models/schema before services
- Services before API routes
- Backend before frontend wiring (US2)

### Parallel Opportunities

- T002, T003 in Setup can run in parallel
- T006, T007 in Foundational can run in parallel
- All US1 tests (T011–T017) can run in parallel
- All US2 tests (T024–T027) can run in parallel; T031 (badge component) can be built in
  parallel with backend T028–T030
- All US3 tests (T034–T035) can run in parallel
- T038, T039 in Polish can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all US1 tests together:
Task: "Integration test: scanned-readable fixture in backend/tests/integration/test_hardening_scanned_readable.py"
Task: "Integration test: scanned-illegible-page fixture in backend/tests/integration/test_hardening_scanned_illegible.py"
Task: "Integration test: dense/irregular-table fixture in backend/tests/integration/test_hardening_dense_table.py"
Task: "Integration test: multi-language fixture in backend/tests/integration/test_hardening_multilanguage.py"
Task: "Integration test: poor-quality-scan fixture in backend/tests/integration/test_hardening_poor_quality_scan.py"
Task: "Unit test: confidence bucketing in backend/tests/unit/test_confidence.py"
Task: "Unit test: document status rollup in backend/tests/unit/test_document_status.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Run quickstart.md Scenario 1 against all hardening fixtures
5. Deploy/demo if ready — this alone satisfies the core "no document left stuck or silently
   unusable" guarantee (SC-001, SC-002)

### Incremental Delivery

1. Setup + Foundational → confidence/error infrastructure ready
2. User Story 1 → every document reaches a correct outcome → validate → deploy (MVP)
3. User Story 2 → inspection views surface confidence accurately → validate → deploy
4. User Story 3 → failure reasons become specific/distinguishable → validate → deploy
5. Polish → determinism + crash-safety guarantees + full quickstart validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- This is a hardening slice: most implementation tasks modify existing
  002-document-processing-pipeline files in place rather than creating new modules, aside from
  `confidence.py`, `errors.py` (new), and the hardening fixtures/tests
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
