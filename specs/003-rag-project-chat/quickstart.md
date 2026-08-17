# Quickstart: RAG Project Chat

This guide validates project-scoped RAG chat end-to-end: grounded answers with citations,
table/image attachment, multi-thread history, live retrieving/generating feedback, and
isolation.

## Prerequisites

- 001-core-foundation and 002-document-processing-pipeline deployed and working (auth,
  projects, RLS baseline, and at least one project with fully "stored" documents containing
  text, a table, and an image).
- Supabase Postgres migrated with `messages` and `message_citations` tables (see
  [data-model.md](./data-model.md)) and RLS policies applied.
- Backend `.env` configured with the same Gemini API key used in
  002-document-processing-pipeline (chat/generation access, in addition to the multimodal
  summarization access already configured).
- Test project containing: a document with a clearly answerable text fact, a document with a
  table, and a document with an image — all at "stored" status.

## Setup

```bash
# Backend (assumes 001/002 backend already running)
cd backend
uvicorn app.main:app --reload

# Frontend (assumes 001/002 frontend already running)
cd frontend
npm run dev
```

## Validation Scenarios

### 1. Grounded, traceable answer (User Story 1)

1. Open the test project's chat and ask a question whose answer is clearly present in the
   text document.
2. Confirm the response includes the answer text plus a visible source citation (document +
   page/section).
3. Ask a question unrelated to any uploaded document's content.
4. Confirm the response clearly states insufficient information was found, rather than
   producing an unsupported answer.

**Expected**: 100% of answers carry a citation or an explicit insufficient-evidence
indication (SC-001).

### 2. Table/image displayed in response (User Story 2)

1. Ask a question whose best-supporting evidence is the table document.
2. Confirm the response displays the original table (not only a text description).
3. Ask a question whose best-supporting evidence is the image document.
4. Confirm the response displays the original image.

**Expected**: 100% of table/image-grounded answers show the original asset (SC-003).

### 3. Multiple independent conversation threads (User Story 3)

1. Create two threads in the same project.
2. Ask different questions in each.
3. Switch between threads and confirm each shows only its own message history.
4. Reload the page and confirm both threads' histories are still intact.

**Expected**: Thread switch loads correct history in <2s (SC-006); no cross-thread
contamination.

### 4. Retrieving vs. generating feedback, non-blocking (User Story 4)

1. Ask a question and observe the UI show a "retrieving" indicator immediately, then a
   "generating" indicator once retrieval completes.
2. While the answer is still generating, switch to a different project or thread and confirm
   the app remains fully responsive.
3. Confirm the original question's answer completes and appears correctly in its original
   thread even after navigating away and back.

**Expected**: Retrieving indicator within 1s (SC-004); app remains usable throughout 100% of
generations (SC-007); FR-019 background-completion behavior confirmed.

### 5. Concurrent messages in the same thread

1. Send a question, and immediately (before the first answer finishes) send a second question
   in the same thread.
2. Confirm both messages appear in the correct order with no loss, duplication, or
   misordering, and both eventually receive their own answers.

**Expected**: 0 instances of message loss/duplication/misordering (SC-008).

### 6. Cross-project isolation

1. Using a second project (with different documents), ask a question there.
2. Confirm the answer is never grounded in the first project's documents, and no citation
   ever references the first project's documents.

**Expected**: 0 instances of cross-project grounding (SC-005).

### 7. Generation failure handling

1. Simulate a generation failure/timeout (e.g., via a test double or fault injection on the
   Gemini call) after retrieval has completed.
2. Confirm the specific message shows a clear failed state with a reason, and the rest of the
   thread's history remains intact and uncorrupted.

**Expected**: Matches FR-016; no thread-history corruption.

## Automated Test Coverage (see plan.md Project Structure)

- `backend/tests/unit/` — retriever project-scoping, citation assembly, context assembly.
- `backend/tests/integration/` — grounded-answer, insufficient-evidence, table/image
  attachment, cross-project isolation, concurrent-message ordering, generation-failure tests.
- `backend/tests/contract/` — request/response and SSE event-shape tests per
  [contracts/api.md](./contracts/api.md).
- `frontend/tests/e2e/` — Playwright flows mirroring scenarios 1–7 above.
