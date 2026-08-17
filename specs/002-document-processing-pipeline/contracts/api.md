# API Contract: Document Processing Pipeline

All endpoints require a valid Supabase JWT (`Authorization: Bearer <token>`) and are scoped
under an owned project. Requests referencing a project or document the caller does not own
receive `404 Not Found` (never `403`), consistent with 001-core-foundation's contract rules.

## POST /api/v1/projects/{project_id}/documents

Upload a document into a project. Accepts `multipart/form-data`.

**Responses**:
- `202 Accepted` — document created with status `uploaded` (immediately transitioning to
  `queued`); returns `{ "id", "filename", "file_type", "status", "uploaded_at" }`. Returns
  before processing begins (SC-007: <2s).
- `422 Unprocessable Entity` — unsupported file type/format (FR-002), with a specific reason.
- `404 Not Found` — project not found or not owned by caller.
- `401 Unauthorized` — missing/invalid JWT.

---

## GET /api/v1/projects/{project_id}/documents

List documents in a project with their current status.

**Responses**:
- `200 OK` — array of `{ "id", "filename", "file_type", "status", "failure_reason",
  "uploaded_at", "updated_at" }`, scoped strictly to `project_id` and its owner.
- `404 Not Found` — project not found or not owned by caller.
- `401 Unauthorized` — missing/invalid JWT.

---

## GET /api/v1/projects/{project_id}/documents/{document_id}

Retrieve a single document's current status/detail summary.

**Responses**:
- `200 OK` — document fields plus `element_count` and `element_counts_by_type` (e.g.,
  `{ "text": 30, "table": 5, "image": 7 }`), computed from persisted `elements` rows (FR-016),
  no re-processing triggered (FR-018).
- `404 Not Found` — document, or its project, not found/not owned.
- `401 Unauthorized` — missing/invalid JWT.

---

## GET /api/v1/projects/{project_id}/documents/{document_id}/elements

List an individual document's elements with per-element metadata (FR-017).

**Responses**:
- `200 OK` — array of `{ "id", "element_type", "page_number", "sequence_index",
  "raw_text" (nullable), "summary" (nullable, for table/image), "asset_reference_url"
  (nullable, for table/image) }`.
- `404 Not Found` — document/project not found or not owned.
- `401 Unauthorized` — missing/invalid JWT.

---

## GET /api/v1/projects/{project_id}/documents/{document_id}/asset-references/{asset_reference_id}

Retrieve a signed/scoped URL (or redirect) to redisplay an original table/image asset (FR-011).

**Responses**:
- `200 OK` — `{ "url", "expires_at" }` (or equivalent), scoped to the requesting user's
  ownership of the parent project.
- `404 Not Found` — asset, document, or project not found/not owned.
- `401 Unauthorized` — missing/invalid JWT.

---

## GET /api/v1/projects/{project_id}/documents/status-stream

Server-Sent Events stream of processing status changes for all documents in the project
(FR-007, FR-023).

**Behavior**:
- On connect, immediately emits one `status` event per currently in-flight (non-terminal)
  document reflecting its true current stage (recovers state after reload/reconnect, FR-008,
  FR-023).
- Thereafter emits a `status` event `{ "document_id", "stage", "occurred_at", "reason"
  (nullable) }` whenever a new `processing_status_events` row is inserted for a document in
  this project.
- Connection scoped strictly to the authenticated caller's ownership of `project_id`; no
  events for other projects/users are ever sent on this stream.

**Responses**:
- `200 OK` — `text/event-stream`, held open until the client disconnects.
- `404 Not Found` — project not found or not owned by caller.
- `401 Unauthorized` — missing/invalid JWT (validated at connection time; Supabase JWTs used
  as short-lived bearer tokens, not embedded as query params where they could leak into logs).

---

## Cross-Cutting Contract Rules

- Every path containing `{project_id}` and/or `{document_id}` MUST be validated against the
  authenticated caller's ownership (transitively for `documents` → `projects`) before any
  nested resource (elements, asset references, status stream) is accessed — implemented via
  shared FastAPI dependencies extending `get_owned_project` from 001-core-foundation.
- No endpoint or stream may emit data belonging to a document/element/chunk from a project the
  caller does not own, under any circumstance, including error responses.
- The status-stream endpoint MUST NOT require polling on the client; the client opens one
  long-lived connection per project and receives all subsequent updates for that project's
  documents through it.
