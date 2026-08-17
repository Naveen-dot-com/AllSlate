# API Contract: RAG Project Chat

All endpoints require a valid Supabase JWT and are scoped under an owned project and, where
applicable, an owned conversation thread. Requests referencing a project or thread the caller
does not own receive `404 Not Found` (never `403`), consistent with prior slices.

## POST /api/v1/projects/{project_id}/conversations

Start a new conversation thread within a project (extends the endpoint stubbed in
001-core-foundation's contract; now fully backed by this feature's message model).

**Responses**:
- `201 Created` — `{ "id", "project_id", "title" (nullable), "created_at" }`.
- `404 Not Found` — project not found or not owned by caller.
- `401 Unauthorized` — missing/invalid JWT.

---

## GET /api/v1/projects/{project_id}/conversations/{conversation_id}/messages

List a thread's full message history in order (FR-011, FR-012).

**Responses**:
- `200 OK` — array of `{ "id", "sequence_number", "role", "content", "status",
  "failure_reason", "is_grounded", "created_at", "citations": [ { "document_id", "page_number"
  (nullable), "asset_reference_url" (nullable) } ] }`, ordered by `sequence_number`.
- `404 Not Found` — conversation/project not found or not owned by caller.
- `401 Unauthorized` — missing/invalid JWT.

---

## POST /api/v1/projects/{project_id}/conversations/{conversation_id}/ask

Submit a natural-language question and receive a streamed, grounded answer (FR-001).

**Request body**: `{ "question": "string, required" }`

**Response**: `200 OK`, `text/event-stream` (SSE). Event sequence:

1. `phase` event — `{ "phase": "retrieving" }` (FR-014), emitted immediately (target: within 1s).
2. `phase` event — `{ "phase": "generating" }`, emitted once retrieval completes.
3. Zero or more `token` events — `{ "delta": "string" }` (incremental answer text), OR a
   single `insufficient_evidence` event if no chunks met the relevance threshold (FR-005),
   skipping generation entirely.
4. Terminal event — either:
   - `complete` — `{ "message_id", "content", "citations": [ { "document_id", "page_number",
     "asset_reference_url" (nullable) } ], "is_grounded" }`, or
   - `failed` — `{ "message_id", "failure_reason" }` (FR-016).

**Error responses** (before streaming begins):
- `404 Not Found` — conversation/project not found or not owned by caller.
- `401 Unauthorized` — missing/invalid JWT.
- `422 Unprocessable Entity` — empty/invalid question text.

**Behavior notes**:
- The user's question is persisted as a `messages` row (`role: user`, `status: complete`)
  before the stream begins, guaranteeing it is never lost even if generation later fails
  (FR-018).
- If the client disconnects mid-stream (e.g., navigates away), generation continues
  server-side and the final `messages` row is still persisted and correctly associated with
  this thread (FR-019); a subsequent call to the messages-list endpoint will show the
  completed (or failed) message.
- Concurrent calls to this endpoint for the same `conversation_id` are each assigned a
  strictly increasing `sequence_number`; none are dropped, duplicated, or reordered (FR-018).

---

## Cross-Cutting Contract Rules

- Every path containing `{project_id}` and/or `{conversation_id}` MUST be validated against
  the authenticated caller's ownership before retrieval, generation, or history access occurs
  — implemented via shared FastAPI dependencies extending `get_owned_project` (and a new
  `get_owned_conversation`) from prior slices.
- The `ask` endpoint's retrieval step MUST NOT be able to return chunks from any project other
  than the one identified by `{project_id}` in the path, under any circumstance.
- No response (including `failed` events) may include content, citations, or error details
  belonging to another user's or project's data.
