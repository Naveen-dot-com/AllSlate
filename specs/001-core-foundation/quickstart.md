# Quickstart: Core Application Foundation

This guide validates the core foundation slice end-to-end: sign-in, first-project
onboarding, project management, isolation, and dedicated project chat.

## Prerequisites

- Supabase project configured with:
  - Google OAuth provider enabled (Client ID/Secret configured in Supabase Auth settings).
  - Postgres schema migrated with `user_profiles`, `projects`, `conversations`, `messages`
    tables and RLS policies (see [data-model.md](./data-model.md)).
- Backend `.env` configured with the Supabase project URL and JWT secret/JWKS endpoint (never
  committed to source control).
- Frontend `.env.local` configured with the Supabase project URL and public anon key.
- Two test Google accounts available (to validate cross-user isolation).

## Setup

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Validation Scenarios

### 1. Sign-in and session persistence (User Story 1)

1. Open the frontend in a browser while signed out.
2. Confirm you are redirected to the sign-in screen and cannot view any project data by
   navigating directly to a project URL.
3. Sign in with a Google test account.
4. Confirm a `user_profiles` row now exists for this account (create-or-retrieve, FR-002).
5. Refresh the page — confirm you remain signed in (FR-003).
6. Sign out — confirm you're returned to the sign-in screen and further navigation is
   blocked (FR-004).

**Expected**: All steps pass with no unauthenticated access to project/chat data
(SC-001).

### 2. First-time onboarding into project creation (User Story 2)

1. Sign in with a brand-new Google account that has never signed in before.
2. Confirm you are guided directly into a "create your first project" flow rather than an
   empty project list.

**Expected**: Matches FR-006; completes within the 60-second target of SC-002.

### 3. Project create/list/switch (User Story 3)

1. Create two projects with distinct names and descriptions.
2. Confirm both appear in the project list, each showing name, description, and active-state
   indicator.
3. Switch the active project and confirm the chat view updates accordingly.
4. Refresh the browser and confirm both projects are still listed and reopenable.

**Expected**: Matches FR-007–FR-012; switch completes in under 2 seconds (SC-004).

### 4. Cross-project and cross-user isolation (User Story 4)

1. Using account A, note the `project_id` of one of its projects.
2. Using account B (a different Google account), attempt to fetch
   `GET /api/v1/projects/{account_A_project_id}` with account B's JWT.
3. Confirm the response is `404 Not Found` (not `403`), disclosing nothing about the
   project's existence (FR-015).
4. Confirm account B's project list never includes account A's projects (FR-016, FR-018).
5. Repeat for `conversations` and `messages` endpoints nested under account A's project.

**Expected**: Zero cross-tenant data exposure in any response (SC-003).

### 5. Dedicated per-project chat (User Story 5)

1. Open a brand-new project with no prior conversations — confirm the chat view shows an
   empty state, not another project's history (FR-021, FR-022).
2. Start a conversation thread in Project A; switch to Project B and confirm Project B's chat
   view does not show Project A's messages.

**Expected**: Matches FR-021/FR-022 and the acceptance scenarios of User Story 5.

## Automated Test Coverage (see plan.md Project Structure)

- `backend/tests/integration/` — RLS + ownership isolation tests (simulate two users' JWTs
  against the same Postgres instance).
- `backend/tests/contract/` — request/response contract tests per [contracts/api.md](./contracts/api.md).
- `frontend/tests/e2e/` — Playwright flows mirroring scenarios 1–5 above.
