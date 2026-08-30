# Tasks: Core Application Foundation

**Input**: Design documents from `/specs/001-core-foundation/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/api.md](./contracts/api.md), [quickstart.md](./quickstart.md)

**Tests**: Included for auth, onboarding, project management, isolation, and chat flows to keep each user story independently verifiable.

**Organization**: Tasks are grouped by user story so each story can be implemented, tested, and validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare the backend/frontend structure, dependency wiring, and shared configuration for the foundation slice.

- [ ] T001 Create the backend application structure and domain folders in `backend/app/api/`, `backend/app/models/`, `backend/app/services/`, `backend/app/db/`, and `backend/migrations/`
- [ ] T002 [P] Initialize the backend Python environment and FastAPI/Pydantic configuration in `backend/requirements.txt` and `backend/app/main.py`
- [X] T003 [P] Initialize the frontend Next.js App Router shell, theme provider, and design-system entry points in `frontend/app/`, `frontend/components/`, and `frontend/lib/`
- [ ] T004 [P] Add shared environment/config validation for Supabase credentials and app settings in `backend/app/config.py` and `frontend/lib/supabase/config.ts`

**Checkpoint**: Project structure and shared configuration exist; backend and frontend can be developed in parallel.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the core auth, database, and security scaffolding that all user stories depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T005 Create the Supabase/Postgres migration for `user_profiles`, `projects`, `conversations`, and `messages` tables in `backend/migrations/001_core_foundation.sql`
- [ ] T006 [P] Add row-level-security policies and ownership checks for `projects`, `conversations`, and `messages` in `backend/migrations/001_core_foundation.sql`
- [ ] T007 [P] Implement the user/profile and project/conversation Pydantic models in `backend/app/models/` with validation for required fields and length limits
- [ ] T008 Implement JWT extraction and authentication dependency logic in `backend/app/api/deps.py`
- [ ] T009 [P] Implement project ownership enforcement and access gating in `backend/app/api/deps.py` and `backend/app/services/project_access.py`
- [ ] T010 Create the shared Supabase client and server-side auth helpers in `frontend/lib/supabase/client.ts`, `frontend/lib/supabase/server.ts`, and `frontend/lib/supabase/auth.ts`
- [ ] T011 Add structured logging and error responses for auth failures and unauthorized project access in `backend/app/services/error_handling.py` and `backend/app/main.py`

**Checkpoint**: Auth, project ownership, and database isolation scaffolding are ready; user story work can proceed.

---

## Phase 3: User Story 1 - Sign In and Reach My Workspace (Priority: P1) 🎯 MVP

**Goal**: A user can access an authenticated workspace, stay signed in across refreshes, and be blocked when not authenticated.

**Independent Test**: Open the app signed out, confirm access is blocked, complete Google sign-in, refresh the page, and confirm the session persists; sign out and verify access is revoked.

### Tests for User Story 1

- [ ] T012 [P] [US1] Contract test: unauthenticated requests receive `401` and protected routes are rejected in `backend/tests/contract/test_auth.py`
- [ ] T013 [P] [US1] E2E test: sign-in, refresh persistence, and sign-out flow in `frontend/tests/e2e/auth.spec.ts`

### Implementation for User Story 1

- [ ] T014 [US1] Implement the Google sign-in screen and auth redirect handling in `frontend/app/(auth)/sign-in/page.tsx`
- [ ] T015 [US1] Add session persistence and sign-out logic to the Supabase auth layer in `frontend/lib/supabase/auth.ts` and `frontend/components/auth/session-provider.tsx`
- [ ] T016 [US1] Add authenticated app-shell guard and route protection in `frontend/app/(app)/layout.tsx` and `frontend/middleware.ts`
- [ ] T017 [US1] Implement the backend profile bootstrap endpoint and upsert logic in `backend/app/api/routes/auth.py` and `backend/app/services/user_profile.py`
- [ ] T018 [US1] Create the authenticated user state contract and client bootstrap flow in `frontend/lib/api/auth-client.ts` and `frontend/app/layout.tsx`
- [ ] T019 [US1] Add no-secret and no-client-credential safeguards to the frontend config and backend settings in `backend/app/config.py` and `frontend/lib/supabase/config.ts`

**Checkpoint**: Signed-out users cannot access app data; signed-in users stay authenticated and can reach the workspace.

---

## Phase 4: User Story 2 - First-Time User Is Guided to Create a Project (Priority: P1)

**Goal**: A first-time user is guided directly into creating their first project instead of facing an empty or ambiguous workspace.

**Independent Test**: Sign in as a brand-new user with zero projects and confirm the onboarding flow opens the project-creation path.

### Tests for User Story 2

- [ ] T020 [P] [US2] E2E test: zero-project onboarding redirects to first-project creation in `frontend/tests/e2e/onboarding.spec.ts`
- [ ] T021 [P] [US2] Contract test: first-time user profile and project bootstrap state is correct in `backend/tests/contract/test_onboarding.py`

### Implementation for User Story 2

- [ ] T022 [US2] Implement the first-run project detection and onboarding redirect in `frontend/app/(app)/page.tsx` and `frontend/components/projects/empty-state.tsx`
- [ ] T023 [US2] Build the first-project creation flow in `frontend/app/(app)/projects/new/page.tsx` and `frontend/components/projects/project-form.tsx`
- [ ] T024 [US2] Implement the backend project creation endpoint and validation in `backend/app/api/routes/projects.py`
- [ ] T025 [US2] Add project creation service logic for empty name rejection and owner assignment in `backend/app/services/projects.py`
- [ ] T026 [US2] Ensure the project list view displays the correct empty state for zero-project users in `frontend/components/projects/project-list.tsx`

**Checkpoint**: New users can immediately create a first project and no longer face an empty, unusable workspace.

---

## Phase 5: User Story 3 - Create, View, and Switch Between Projects (Priority: P1)

**Goal**: Authenticated users can create, list, reopen, and switch between their own projects while seeing active-project state clearly.

**Independent Test**: Create multiple projects with different names/descriptions, switch the active project, and confirm the list and context update correctly.

### Tests for User Story 3

- [ ] T027 [P] [US3] Contract test: project create/list/get endpoints return expected data and validation errors in `backend/tests/contract/test_projects.py`
- [ ] T028 [P] [US3] E2E test: create/list/switch projects across multiple active contexts in `frontend/tests/e2e/projects.spec.ts`

### Implementation for User Story 3

- [ ] T029 [US3] Implement project create/list/get endpoints in `backend/app/api/routes/projects.py`
- [ ] T030 [US3] Add project service logic for retrieval, ordering, validation, and active-context tracking in `backend/app/services/projects.py`
- [ ] T031 [US3] Build the project list and active-project UI in `frontend/components/projects/project-list.tsx` and `frontend/components/projects/project-card.tsx`
- [ ] T032 [US3] Add the project creation and switch interactions in `frontend/app/(app)/projects/page.tsx`
- [ ] T033 [US3] Persist the current active project in a client-side app state or route param store in `frontend/lib/project-context.ts` and related UI state files
- [ ] T034 [US3] Add validation and error messaging for empty or overlong project names/descriptions in `frontend/components/projects/project-form.tsx`

**Checkpoint**: Project management is functional and independently testable as a complete user flow.

---

## Phase 6: User Story 4 - Projects Are Fully Isolated From Each Other and Other Users (Priority: P1)

**Goal**: All project- and conversation-scoped operations are denied across users and across projects, even when IDs are guessed or modified.

**Independent Test**: Using two users and two projects, confirm that a project owned by user A cannot be accessed by user B and that no project data leaks in any API response or UI view.

### Tests for User Story 4

- [ ] T035 [P] [US4] Integration test: cross-user access to another project's data is rejected in `backend/tests/integration/test_project_isolation.py`
- [ ] T036 [P] [US4] Contract test: unauthorized access uses `404` semantics and never exposes project existence in `backend/tests/contract/test_ownership_enforcement.py`

### Implementation for User Story 4

- [ ] T037 [US4] Harden the API dependency chain so every project-scoped route validates auth and project ownership before access in `backend/app/api/deps.py`
- [ ] T038 [US4] Add database-layer isolation policies to enforce project ownership via RLS in `backend/migrations/001_core_foundation.sql`
- [ ] T039 [US4] Add API tests and failure handling for invalid/mismatched project IDs in `backend/tests/contract/` and `backend/app/services/project_access.py`
- [ ] T040 [US4] Update the frontend API client and app views to prevent stale or cross-project rendering when a user has no access to a project in `frontend/lib/api/client.ts` and `frontend/app/(app)/projects/[projectId]/layout.tsx`
- [ ] T041 [US4] Add defensive UI/error states for project-not-found or unauthorized access without leaking cross-tenant details in `frontend/components/error/project-access-error.tsx`

**Checkpoint**: Project and user isolation is enforced at both API and database layers; no cross-tenant leakage is possible.

---

## Phase 7: User Story 5 - Dedicated Chat Per Project (Priority: P2)

**Goal**: Each project exposes a dedicated, project-scoped chat experience with empty-state handling and project-aware conversation view.

**Independent Test**: Open a project and confirm the chat view belongs to that project; switch to another project and confirm the previous project's chat history is not shown.

### Tests for User Story 5

- [ ] T042 [P] [US5] E2E test: project-specific chat view and empty state in `frontend/tests/e2e/chat.spec.ts`
- [ ] T043 [P] [US5] Contract test: conversation listing and message retrieval are scoped to the current project in `backend/tests/contract/test_conversations.py`

### Implementation for User Story 5

- [ ] T044 [US5] Implement the conversation and messages model schema and validation in `backend/app/models/conversation.py` and `backend/app/models/message.py`
- [ ] T045 [US5] Implement conversation creation and listing endpoints in `backend/app/api/routes/conversations.py`
- [ ] T046 [US5] Implement project-scoped chat data retrieval for messages in `backend/app/services/conversations.py`
- [ ] T047 [US5] Build the empty-state project chat UI in `frontend/app/(app)/projects/[projectId]/chat/page.tsx` and `frontend/components/chat/chat-empty-state.tsx`
- [ ] T048 [US5] Wire the active project to the chat route and ensure switching projects updates the visible conversation context in `frontend/app/(app)/projects/[projectId]/layout.tsx` and `frontend/components/chat/chat-shell.tsx`
- [ ] T049 [US5] Add project-specific conversation list and message state handling in `frontend/lib/api/conversations.ts`

**Checkpoint**: Each project has its own dedicated chat view and chat state remains isolated from other projects.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final quality work across the entire feature: consistency, validation, and a complete onboarding-to-chat flow.

- [ ] T050 [P] Add project-level documentation and onboarding notes in `README.md` and the feature-specific docs under `specs/001-core-foundation/`
- [ ] T051 [P] Run backend unit/integration tests for auth, project management, ownership enforcement, and chat scope in `backend/tests/`
- [ ] T052 [P] Run frontend smoke/E2E validation for sign-in, project onboarding, list/switch flows, and project chat in `frontend/tests/`
- [ ] T053 Confirm the app matches the quickstart validation scenarios in `specs/001-core-foundation/quickstart.md`
- [ ] T054 Final cleanup and accessibility pass across the authenticated app shell, project list, and chat components in `frontend/components/` and `frontend/app/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user story work.
- **User Stories (Phases 3–7)**: All depend on the foundation phase, then proceed in priority order.
- **Polish (Phase 8)**: Depends on all required user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational; required before any workspace flow is usable.
- **User Story 2 (P1)**: Depends on US1 and the project model; no parallel dependency on US3/US4 if implemented by separate team members.
- **User Story 3 (P1)**: Depends on US1 and US2 for project creation flow; can proceed in parallel with US4 security work after the API contract is stable.
- **User Story 4 (P1)**: Depends on core auth and project ownership rules; should be implemented alongside US3.
- **User Story 5 (P2)**: Depends on US3 and project isolation being complete.

### Parallel Opportunities

- Setup tasks T002–T004 can run in parallel after the repo structure is in place.
- Foundational tasks T006–T011 can run in parallel within the security and API scaffolding boundary.
- Story tests and model tasks within each user story can run in parallel once the foundational phase is complete.
- US3 and US4 can be worked in parallel by separate owners once the project API contract and ownership dependencies are stable.

### Parallel Example

```bash
# Launch the main auth and backend foundation tasks together
Task: "Create Supabase/Postgres migration ... in backend/migrations/001_core_foundation.sql"
Task: "Implement JWT extraction and authentication dependency logic in backend/app/api/deps.py"
Task: "Create the shared Supabase client and auth helpers in frontend/lib/supabase/"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Validate the login, session, and protected-route flow end-to-end
5. Then continue to User Story 2 and User Story 3 for the full workspace foundation

### Incremental Delivery

- Deliver US1 + US2 + US3 as the first usable foundation slice for workspace onboarding and project management.
- Deliver US4 as the security hardening milestone before shipping any production-facing project data.
- Deliver US5 as the final project-level chat integration once isolation and navigation are proven stable.
