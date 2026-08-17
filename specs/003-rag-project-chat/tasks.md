# Tasks: RAG Project Chat

**Input**: Design documents from `/specs/003-rag-project-chat/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and verification of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the reusable project structure and testing scaffolding required by the chat feature.

- [ ] T001 Create backend chat and retrieval module structure in backend/app/api/routes/chat.py, backend/app/rag/, backend/app/services/, and backend/app/models/
- [ ] T002 [P] Initialize backend Python dependencies for FastAPI, LangChain, pgvector, Supabase, and Gemini integration in backend/requirements.txt or backend/pyproject.toml
- [ ] T003 [P] Initialize frontend chat state and SSE client scaffolding in frontend/lib/chat/ and frontend/components/chat/
- [ ] T004 [P] Configure pytest, Vitest/Playwright, and shared test directories under backend/tests/ and frontend/tests/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the storage, validation, and shared retrieval primitives that all later stories depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T005 Create Pydantic models for `Message`, `MessageCitation`, and `RetrievalResult` in backend/app/models/chat_models.py
- [ ] T006 Implement project/thread ownership validation and shared FastAPI dependencies in backend/app/api/deps.py and backend/app/api/routes/chat.py
- [ ] T007 Add database migration for `messages` and `message_citations` tables with RLS in backend/migrations/003_rag_project_chat.sql
- [ ] T008 Implement project-scoped pgvector retrieval and metadata filter generation in backend/app/rag/retriever.py
- [ ] T009 [P] Implement shared error handling, logging, and SSE event serialization in backend/app/core/errors.py and backend/app/core/sse.py
- [ ] T010 [P] Create backend service layer for message creation, history fetch, and ordered inserts in backend/app/services/chat_service.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Ask a Question and Get a Grounded, Traceable Answer (Priority: P1) 🎯 MVP

**Goal**: Enable a user to ask a project-scoped question and receive a grounded answer with source citations and clear insufficient-evidence handling.

**Independent Test**: Ask a question whose answer exists in uploaded project documents and verify the response includes a visible citation and the correct source metadata; ask an unrelated question and verify the system returns an explicit insufficient-evidence response instead of guessing.

### Tests for User Story 1

- [ ] T011 [P] [US1] Contract test for POST /api/v1/projects/{project_id}/conversations/{conversation_id}/ask in backend/tests/contract/test_chat_ask.py
- [ ] T012 [P] [US1] Integration test for grounded answer + insufficient-evidence paths in backend/tests/integration/test_chat_grounded_answers.py
- [ ] T013 [P] [US1] Unit test for project-scoped retrieval and citation assembly in backend/tests/unit/test_rag_retriever.py

### Implementation for User Story 1

- [ ] T014 [P] [US1] Implement document context assembly and citation indexing in backend/app/rag/context_assembly.py
- [ ] T015 [US1] Implement citation mapping and asset-reference resolution in backend/app/rag/citations.py
- [ ] T016 [US1] Implement ask-question SSE stream, phase transitions, and answer persistence in backend/app/api/routes/chat.py
- [ ] T017 [US1] Add retrieval + generation orchestration logic and insufficient-evidence short-circuit in backend/app/rag/generation.py
- [ ] T018 [US1] Persist user and assistant messages with status lifecycle and citation rows in backend/app/services/chat_service.py
- [ ] T019 [US1] Add backend validation for empty questions, missing project/thread ownership, and failed generation states in backend/app/api/routes/chat.py

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - See the Original Table or Image, Not Just a Description (Priority: P1)

**Goal**: When evidence comes from a table or image, the response shows the original asset and ties it back to the answer and citations.

**Independent Test**: Ask a question whose best support is a table or image and verify the original asset is displayed in the response alongside the answer.

### Tests for User Story 2

- [ ] T020 [P] [US2] Integration test for table/image attachment in backend/tests/integration/test_chat_assets.py
- [ ] T021 [P] [US2] Unit test for asset-reference lookup and response payload shaping in backend/tests/unit/test_rag_citations.py

### Implementation for User Story 2

- [ ] T022 [P] [US2] Implement message content renderer for citations and attached table/image assets in frontend/components/chat/message-content.tsx
- [ ] T023 [US2] Add frontend SSE chat state handling to surface asset URLs returned with answer payloads in frontend/lib/chat/use-chat-stream.ts
- [ ] T024 [US2] Render original tables and images within assistant message cards in frontend/app/(app)/projects/[projectId]/chat/[threadId]/page.tsx
- [ ] T025 [US2] Add front-end styling and metadata mapping for citation chips and asset attachments in frontend/components/chat/citation-chip.tsx and frontend/components/chat/asset-preview.tsx

**Checkpoint**: At this point, User Stories 1 and 2 should both work independently.

---

## Phase 5: User Story 3 - Maintain Multiple Independent Conversation Threads Per Project (Priority: P2)

**Goal**: Support multiple project-scoped chat threads with independent message histories and thread switching.

**Independent Test**: Create two threads in the same project, ask different questions in each, switch between threads, and verify each thread shows only its own message history.

### Tests for User Story 3

- [ ] T026 [P] [US3] Integration test for thread isolation and persistence in backend/tests/integration/test_chat_threads.py
- [ ] T027 [P] [US3] End-to-end test for multi-thread switching in frontend/tests/e2e/chat-threads.spec.ts

### Implementation for User Story 3

- [ ] T028 [P] [US3] Implement new conversation creation and history endpoints in backend/app/api/routes/chat.py
- [ ] T029 [US3] Implement thread history retrieval service and ordered message serialization in backend/app/services/conversation_service.py
- [ ] T030 [US3] Add thread list and switch state to the project chat shell in frontend/app/(app)/projects/[projectId]/chat/page.tsx
- [ ] T031 [US3] Add thread-specific message loading and local state updates in frontend/app/(app)/projects/[projectId]/chat/[threadId]/page.tsx

**Checkpoint**: At this point, User Stories 1, 2, and 3 should be independently functional.

---

## Phase 6: User Story 4 - Responsive Chat With Clear Retrieval vs. Generation Feedback (Priority: P2)

**Goal**: Keep the application responsive while visually distinguishing retrieval from generation and handling concurrent or background work safely.

**Independent Test**: Submit a question and confirm the UI shows a distinct retrieving state, then a distinct generating state, while the rest of the app remains responsive and the message history still orders correctly under concurrent activity.

### Tests for User Story 4

- [ ] T032 [P] [US4] End-to-end test for retrieving/generating status and non-blocking interactions in frontend/tests/e2e/chat-status.spec.ts
- [ ] T033 [P] [US4] Integration test for concurrent message ordering and background completion in backend/tests/integration/test_chat_concurrency.py

### Implementation for User Story 4

- [ ] T034 [P] [US4] Add phase events and streamed status handling in backend/app/rag/generation.py
- [ ] T035 [US4] Implement front-end retrieval/generation status UI and progress indicators in frontend/components/chat/chat-status.tsx
- [ ] T036 [US4] Ensure new-message sequencing and background completion are safe within a thread in backend/app/services/chat_service.py
- [ ] T037 [US4] Update navigation and chat-state behavior to remain responsive during in-flight generation in frontend/lib/chat/use-chat-stream.ts and frontend/app/(app)/projects/[projectId]/chat/page.tsx

**Checkpoint**: All core user stories should now be independently functional and externally testable.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final hardening, validation, and release-readiness work across all stories.

- [ ] T038 [P] Validate the end-to-end quickstart scenarios against specs/003-rag-project-chat/quickstart.md and fix gaps
- [ ] T039 [P] Run and update security isolation checks for project-scoped retrieval and RLS enforcement across backend/tests/integration/test_chat_threads.py and backend/tests/integration/test_chat_grounded_answers.py
- [ ] T040 [P] Review and harden error states for failed generations, inaccessible citations, and insufficient-evidence responses in backend/app/rag/ and backend/app/services/
- [ ] T041 Final end-to-end verification across backend and frontend chat flows with repository-level test run and cleanup of remaining regressions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories.
- **User Stories (Phase 3+)**: Depend on Foundational completion.
  - Story 1 can be delivered as the MVP immediately after Foundational.
  - Stories 2 and 4 can proceed in parallel once Story 1 is stable and testable.
  - Story 3 can proceed in parallel with Story 2 and Story 4 if thread and message infrastructure is in place.
- **Polish (Phase 7)**: Depends on all desired stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: No dependency on other stories; it is the primary MVP.
- **User Story 2 (P1)**: Depends on the same retrieval/citation infrastructure as US1 but is independently testable.
- **User Story 3 (P2)**: Depends on the thread/message foundation introduced in Foundational; can proceed in parallel with US2 and US4.
- **User Story 4 (P2)**: Depends on the streaming status infrastructure developed for US1 and the thread-state updates from US3.

### Parallel Opportunities

- Phase 1 Setup tasks T002–T004 can run in parallel.
- Phase 2 Foundational tasks T009–T010 can run in parallel once the core data model and migration tasks are in place.
- Story-specific contract, unit, and integration tests can run in parallel within each story phase.
- UI and backend implementation tasks for different stories can be developed in parallel by separate contributors after the foundation is ready.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Stop and validate the grounded-answer flow before moving to US2–US4.

### Incremental Delivery

1. Setup + Foundational → establish the secure retrieval and persistence foundation.
2. User Story 1 → implement grounded answer generation and traceable citations.
3. User Story 2 → add original table/image handling and asset display.
4. User Story 3 → add multiple conversation-thread support.
5. User Story 4 → add live status feedback and responsiveness guarantees.
6. Polish → final hardening and validation.

### Parallel Team Strategy

With multiple contributors:

1. One engineer can work through the backend foundation and migrations.
2. Another engineer can build the frontend chat client and component scaffolding.
3. A third engineer can prepare story-specific tests and E2E flows while the core backend and frontend are progressing.
4. Once the foundation is complete, teams can deliver US1, US2, US3, and US4 in parallel with clear story boundaries.

---

## Notes

- [P] tasks indicate work that can proceed in parallel across different files and concerns.
- [Story] labels map each task to a specific user story so implementation and verification stay traceable.
- The generated tasks prioritize the core grounded-answer flow first while maintaining explicit independent validation for each story.
- All tasks are tied to concrete files in the repository so they are immediately actionable for implementation.
