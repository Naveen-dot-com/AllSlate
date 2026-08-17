# API Contract: Core Application Foundation

All endpoints are served by the FastAPI backend under a versioned prefix (e.g., `/api/v1`).
Every endpoint below (except health/status, if any) requires a valid Supabase-issued JWT in
the `Authorization: Bearer <token>` header. Requests without a valid JWT receive `401
Unauthorized`. Requests referencing a project the caller does not own receive `404 Not
Found` (never `403`, to avoid disclosing existence of other users' projects per FR-015).

## POST /api/v1/projects

Create a new project owned by the authenticated user.

**Request body**:
```json
{
  "name": "string, 1-200 chars, required",
  "description": "string, up to 2000 chars, optional"
}
```

**Responses**:
- `201 Created` — returns the created project (`id`, `name`, `description`, `owner_id`,
  `created_at`, `updated_at`).
- `422 Unprocessable Entity` — validation error (empty name, overlong fields).
- `401 Unauthorized` — missing/invalid JWT.

---

## GET /api/v1/projects

List all projects owned by the authenticated user.

**Responses**:
- `200 OK` — array of projects (`id`, `name`, `description`, `created_at`, `updated_at`),
  ordered by most recently created or most recently active (implementation detail).
- `401 Unauthorized` — missing/invalid JWT.

**Note**: Only ever returns projects owned by the caller — never another user's projects
(FR-016, FR-018).

---

## GET /api/v1/projects/{project_id}

Retrieve a single project (used when switching/opening a project).

**Responses**:
- `200 OK` — the project details.
- `404 Not Found` — project does not exist OR is not owned by the caller (indistinguishable
  response, per FR-015 edge case).
- `401 Unauthorized` — missing/invalid JWT.

---

## PATCH /api/v1/projects/{project_id}

Update a project's name/description (owner only). *(Included for completeness of the CRUD
surface implied by FR-007/FR-013; not required by a specific user story but supports future
edit-project UX without a schema change.)*

**Request body**: Same shape as create, fields optional (partial update).

**Responses**:
- `200 OK` — updated project.
- `404 Not Found` — not found or not owned.
- `422 Unprocessable Entity` — validation error.
- `401 Unauthorized` — missing/invalid JWT.

---

## POST /api/v1/projects/{project_id}/conversations

Start a new conversation thread within a project.

**Responses**:
- `201 Created` — returns the created conversation (`id`, `project_id`, `title`,
  `created_at`).
- `404 Not Found` — project not found or not owned by caller.
- `401 Unauthorized` — missing/invalid JWT.

---

## GET /api/v1/projects/{project_id}/conversations

List conversation threads for a project (used to populate the project's dedicated chat view).

**Responses**:
- `200 OK` — array of conversations scoped strictly to `project_id`, and only if the project
  is owned by the caller.
- `404 Not Found` — project not found or not owned by caller.
- `401 Unauthorized` — missing/invalid JWT.

---

## GET /api/v1/projects/{project_id}/conversations/{conversation_id}/messages

List messages for a conversation (used to render chat history on project open/switch).

**Responses**:
- `200 OK` — array of messages (`id`, `role`, `content`, `created_at`), ordered chronologically.
- `404 Not Found` — project, conversation, or ownership mismatch (any invalid combination
  returns the same generic 404 to avoid leaking existence details).
- `401 Unauthorized` — missing/invalid JWT.

---

## Cross-Cutting Contract Rules

- Every path containing `{project_id}` MUST be validated against the authenticated caller's
  ownership before touching any nested resource (conversations, messages) — implemented via
  a shared FastAPI dependency (`get_owned_project`), not duplicated per-route logic.
- No endpoint response may include another user's or another project's data under any
  circumstance, including error responses (no stack traces or internal identifiers that could
  reveal cross-tenant information).
- All list endpoints are scoped strictly by the authenticated user + project combination —
  there is no "list all projects" or "list all conversations" admin/global endpoint in this
  slice.
