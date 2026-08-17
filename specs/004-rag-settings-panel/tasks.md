# Tasks: RAG Settings Panel

**Input**: Design documents from `/specs/004-rag-settings-panel/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure for the settings feature across backend and frontend

- [ ] T001 Create backend and frontend feature scaffolding under backend/app/services/, backend/app/api/routes/, backend/tests/, frontend/components/settings-panel/, and frontend/lib/settings/
- [ ] T002 Initialize settings schema and persistence dependencies in backend/app/models/ and backend requirements/configuration used by the RAG chat stack
- [ ] T003 [P] Configure backend and frontend test harnesses for contract, unit, and Playwright coverage for the settings panel

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core settings persistence and query infrastructure that MUST be complete before any user story work can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create the `conversation_settings` table migration and ensure row-level security matches project ownership in backend/migrations/
- [ ] T005 Implement the `ConversationSettings` Pydantic model and field validation in backend/app/models/conversation_settings.py
- [ ] T006 [P] Add default settings creation and lazy-load behavior for conversation thread initialization in backend/app/services/settings_service.py
- [ ] T007 [P] Add authenticated conversation-scoped settings read/write helpers that validate ownership in backend/app/services/settings_service.py and backend/app/api/routes/conversation_settings.py
- [ ] T008 [P] Add GET/PATCH settings endpoint handlers for `/api/v1/projects/{project_id}/conversations/{conversation_id}/settings` in backend/app/api/routes/conversation_settings.py
- [ ] T009 [P] Add ask-time settings resolve flow and effective settings snapshot plumbing into the existing RAG request lifecycle in backend/app/rag/graph.py and backend/app/services/message_service.py
- [ ] T010 Add graceful web-search fallback and citation metadata handling so failures degrade to document-only retrieval in backend/app/rag/web_search.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Discover and Open Retrieval Settings (Priority: P1) 🎯 MVP

**Goal**: Make the settings panel discoverable and understandable from the conversation screen with default values ready to use

**Independent Test**: Open a project's chat screen and confirm a clearly labeled settings panel is visible or easily accessible on the right side without prior knowledge.

### Tests for User Story 1

- [ ] T011 [P] [US1] Add frontend smoke test covering panel discovery and default values in frontend/tests/e2e/settings-discoverability.spec.ts

### Implementation for User Story 1

- [ ] T012 [P] [US1] Create the settings panel shell and right-side glass-panel layout in frontend/components/settings-panel/SettingsPanel.tsx
- [ ] T013 [P] [US1] Add panel open/close state and Knowledge Base labeling in frontend/app/(app)/projects/[projectId]/chat/[threadId]/page.tsx
- [ ] T014 [P] [US1] Create the client settings hook and default state logic in frontend/lib/settings/useConversationSettings.ts
- [ ] T015 [US1] Add accessible labels, helper text, and plain-language descriptions for each control in frontend/components/settings-panel/SettingsControls.tsx

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Toggle Supplementary Web Search (Priority: P1)

**Goal**: Allow a user to enable or disable supplementary web search and ensure the setting takes effect for the next question without a reload

**Independent Test**: Toggle web search on and off, ask a question before and after the toggle, and confirm the behavior changes without reloading the page.

### Tests for User Story 2

- [ ] T016 [P] [US2] Add backend integration test for web-search on/off routing in backend/tests/integration/test_settings_web_search.py
- [ ] T017 [P] [US2] Add E2E test for toggle effect and no-reload behavior in frontend/tests/e2e/settings-web-search.spec.ts

### Implementation for User Story 2

- [ ] T018 [P] [US2] Add `web_search_enabled` validation and persistence to the settings schema in backend/app/models/conversation_settings.py
- [ ] T019 [US2] Implement the conditional LangGraph routing node and web-search branch in backend/app/rag/web_search.py and backend/app/rag/graph.py
- [ ] T020 [P] [US2] Add the frontend web-search toggle and immediate PATCH behavior in frontend/components/settings-panel/SettingsControls.tsx
- [ ] T021 [US2] Ensure the backend falls back to document-only context when web search fails or times out in backend/app/rag/web_search.py

**Checkpoint**: At this point, User Stories 1 and 2 should both work independently

---

## Phase 5: User Story 3 - Adjust Response Creativity (Priority: P2)

**Goal**: Give users a plain-language creativity control that maps to generation temperature for future answers

**Independent Test**: Switch the creativity level from Precise to Creative, ask the same question again, and confirm the new answer reflects the updated level without needing a reload.

### Tests for User Story 3

- [ ] T022 [P] [US3] Add backend integration test covering precise/balanced/creative mapping in backend/tests/integration/test_settings_creativity.py
- [ ] T023 [P] [US3] Add Playwright flow covering creativity updates mid-conversation in frontend/tests/e2e/settings-creativity.spec.ts

### Implementation for User Story 3

- [ ] T024 [P] [US3] Add `creativity_level` validation and mapping to the internal temperature value in backend/app/models/conversation_settings.py
- [ ] T025 [US3] Wire the resolved creativity setting into the generation parameters in backend/app/rag/generation.py and backend/app/rag/graph.py
- [ ] T026 [P] [US3] Add plain-language creativity controls (Precise / Balanced / Creative) to frontend/components/settings-panel/SettingsControls.tsx

**Checkpoint**: User Story 3 should be independently testable without relying on earlier stories

---

## Phase 6: User Story 4 - Tune Retrieval Behavior (Priority: P2)

**Goal**: Let the user adjust retrieval breadth and document-type filters while preserving source fidelity and safe defaults

**Independent Test**: Change both retrieval depth and document-type inclusion, ask a question, and confirm the answer citations reflect the updated retrieval configuration.

### Tests for User Story 4

- [ ] T027 [P] [US4] Add retrieval-specific backend integration test in backend/tests/integration/test_settings_retrieval.py
- [ ] T028 [P] [US4] Add retrieval E2E test covering document-type filter and top-k changes in frontend/tests/e2e/settings-retrieval.spec.ts

### Implementation for User Story 4

- [ ] T029 [P] [US4] Add `retrieval_top_k` and `included_document_types` validation in backend/app/models/conversation_settings.py
- [ ] T030 [US4] Thread retrieval settings into project-document retrieval in backend/app/rag/retriever.py
- [ ] T031 [US4] Add document-type UI controls with zero-selection guard in frontend/components/settings-panel/DocumentTypeFilter.tsx
- [ ] T032 [US4] Enforce at least one included type or fallback to "all known types" in backend/app/services/settings_service.py

**Checkpoint**: User Story 4 should be independently functional and safe by validation

---

## Phase 7: User Story 5 - Settings Apply to the Current Conversation Without Reloading (Priority: P1)

**Goal**: Ensure any setting change is immediately persisted and takes effect for the next question without interrupting the active thread

**Independent Test**: Change a setting while existing conversation history is visible, confirm no reload occurs, and ask a new question that reflects the new setting.

### Tests for User Story 5

- [ ] T033 [P] [US5] Add in-flight-generation regression test in backend/tests/integration/test_settings_inflight.py
- [ ] T034 [P] [US5] Add no-reload history-preservation Playwright test in frontend/tests/e2e/settings-apply-no-reload.spec.ts

### Implementation for User Story 5

- [ ] T035 [US5] Ensure optimistic UI updates and immediate PATCH persistence in frontend/lib/settings/useConversationSettings.ts
- [ ] T036 [US5] Snapshot settings at the start of each ask request and ensure later setting changes do not mutate in-flight answers in backend/app/api/routes/ask.py and backend/app/services/settings_service.py
- [ ] T037 [US5] Persist `effective_settings_snapshot` on assistant messages and preserve historical answers/citations unchanged in backend/app/services/message_service.py

**Checkpoint**: User Story 5 should be independently validated; all P1 stories are complete

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, consistency checks, and product-quality review across all stories

- [ ] T038 [P] Run backend contract and unit test validation for settings API, validation, and routing in backend/tests/contract/test_settings_contract.py and backend/tests/unit/
- [ ] T039 [P] Run frontend settings-panel E2E validation across all settings flows in frontend/tests/e2e/
- [ ] T040 [P] Update feature documentation and validation notes in specs/004-rag-settings-panel/quickstart.md and specs/004-rag-settings-panel/research.md
- [ ] T041 Review security isolation, citation traceability, and RLS correctness across backend/app/services/ and backend/migrations/
- [ ] T042 Complete a dark-mode, accessibility, and glass-panel consistency review for frontend/components/settings-panel/ and frontend/app/(app)/projects/[projectId]/chat/[threadId]/page.tsx

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational completion; MVP baseline for the feature
- **User Story 2 (Phase 4)**: Depends on Foundational completion and can run in parallel with US1 if necessary
- **User Story 3 (Phase 5)**: Depends on Foundational completion and can run in parallel with US1/US2 once the baseline is ready
- **User Story 4 (Phase 6)**: Depends on Foundational completion and can run in parallel with US2/US3
- **User Story 5 (Phase 7)**: Depends on Foundational completion and should run alongside US2/US4 as a regression-focused story
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2; no dependencies on other stories
- **User Story 2 (P1)**: Can start after Phase 2; may integrate with the US1 UI shell
- **User Story 3 (P2)**: Can start after Phase 2; depends on the same settings persistence model as US2
- **User Story 4 (P2)**: Can start after Phase 2; depends on the same settings schema and retrieval pipeline
- **User Story 5 (P1)**: Can start after Phase 2; depends on the same settings persistence and ask flow, but is independently testable

### Parallel Opportunities

- Setup tasks can run in parallel across backend/frontend configuration work
- Foundational tasks can run in parallel where they touch different files or services
- User Story 1 work can proceed in parallel with US2/US3/US4/US5 once the shared foundation is ready
- Tests for a given user story can be written before the implementation work and run in parallel when possible
- Different user stories can be implemented by different developers without blocking each other once the foundation is stable

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Validate the panel discoverability and default-state behavior independently
5. Stop and confirm the panel is usable before expanding to web search, creativity, and retrieval tuning

### Incremental Delivery

1. Complete Setup + Foundational → foundation ready
2. Add User Story 1 → validate panel discoverability
3. Add User Story 2 → validate web-search toggle behavior
4. Add User Story 3 → validate creativity mapping and no-reload apply
5. Add User Story 4 → validate retrieval tuning and guardrails
6. Add User Story 5 → validate safety for in-flight and historical answers
7. Run final polish and regression checks

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
   - Developer D: User Story 4
   - Developer E: User Story 5
3. All stories complete and integrate independently, followed by the final polish phase
