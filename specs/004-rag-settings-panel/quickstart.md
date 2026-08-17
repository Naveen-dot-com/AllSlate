# Quickstart: RAG Settings Panel

This guide validates the settings panel end-to-end: discoverability, web-search toggle,
creativity control, retrieval tuning, immediate application without reload, and isolation
from in-flight/past answers.

## Prerequisites

- 001–003 deployed and working (auth, projects, document processing, and RAG chat with
  streaming, citations, and multi-thread support).
- Supabase Postgres migrated with `conversation_settings` table and the
  `messages.effective_settings_snapshot` column (see [data-model.md](./data-model.md)), with
  RLS applied.
- A web search tool/API credential configured in the backend `.env` (never exposed to the
  frontend).
- A test project with a "stored" document containing at least two distinct element/document
  types (e.g., text and table).

## Setup

```bash
# Backend (assumes 001-003 backend already running)
cd backend
uvicorn app.main:app --reload

# Frontend (assumes 001-003 frontend already running)
cd frontend
npm run dev
```

## Validation Scenarios

### 1. Discover and open the panel (User Story 1)

1. Open a project's chat screen.
2. Confirm a settings panel associated with the Knowledge Base is visible or easily
   accessible on the right side of the screen.
3. Open the panel and confirm each control has a plain-language label/description (no
   unexplained "temperature" or "top-k" jargon shown without context).

**Expected**: Panel is discoverable without instruction (SC-001); controls are
understandable to a non-technical reviewer (SC-002).

### 2. Web search toggle (User Story 2)

1. With web search off (default), ask a question outside the project's document scope; confirm
   the answer indicates insufficient information rather than using external content.
2. Turn web search on; ask the same question again.
3. Confirm the answer may now include externally sourced content, with a distinguishable
   "web" citation, and that this took effect without a page reload.
4. Turn web search back off; confirm subsequent answers no longer include web citations.

**Expected**: 0 external citations while off, across testing (SC-004); setting takes effect
on the very next question (SC-003).

### 3. Creativity control (User Story 3)

1. Set creativity to "Precise," ask a question, and note the answer.
2. Set creativity to "Creative," ask the same question again, and confirm the change is
   applied to this new answer without a reload.

**Expected**: Matches FR-007/FR-008/FR-012.

### 4. Retrieval tuning (User Story 4)

1. Lower `retrieval_top_k` to 1 and ask a broad question; note the citations shown.
2. Raise `retrieval_top_k` to a higher value and ask the same question; confirm more
   citations can appear.
3. Uncheck a document type (e.g., exclude "table"); ask a question whose best evidence is a
   table; confirm the answer's citations never include the excluded type.
4. Attempt to uncheck all document types; confirm the system prevents this with a clear
   message (FR-011).

**Expected**: Matches FR-009/FR-010/FR-011; citations respect the active filter.

### 5. Immediate application without reload (User Story 5)

1. With an existing conversation containing prior messages, change any setting.
2. Confirm the page does not reload and prior message history remains fully intact.
3. Ask a new question and confirm the new setting is already in effect.

**Expected**: 0 page reloads (SC-003); prior history unaffected (FR-014).

### 6. In-flight generation isolation

1. Ask a question that will take a few seconds to answer.
2. While it is still generating, change a setting (e.g., toggle web search).
3. Confirm the in-progress answer completes using the settings that were active when it was
   submitted (check its persisted `effective_settings_snapshot` if inspecting directly), and
   only the next question uses the new setting.

**Expected**: Matches FR-013 and the corresponding edge case.

### 7. Settings persist across panel close/reopen

1. Change several settings, close the panel, and reopen it (without leaving the page).
2. Confirm the previously chosen values are still shown, not reset to defaults.

**Expected**: Matches FR-015.

## Automated Test Coverage (see plan.md Project Structure)

- `backend/tests/unit/` — web-search routing-node decision logic, settings validation
  (empty document-type rejection, out-of-range top_k).
- `backend/tests/integration/` — settings-applied-to-next-question, in-flight-unaffected,
  web-search-fallback-on-failure, document-type-filter-narrows-citations tests.
- `backend/tests/contract/` — settings GET/PATCH contract tests per
  [contracts/api.md](./contracts/api.md).
- `frontend/tests/e2e/` — Playwright flows mirroring scenarios 1–7 above.
