# Data Model: RAG Project Chat

This feature adds two new tables. It reads (but does not modify) `projects`
(001-core-foundation), `conversations` (001-core-foundation, referred to here as
"conversation thread"), and `documents`/`elements`/`chunks`/`asset_references`
(002-document-processing-pipeline).

## Entity: `messages`

Fully implements the `Message` entity referenced (but not detailed) in
001-core-foundation's data model.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | `uuid` | PK, default `gen_random_uuid()` | |
| `conversation_id` | `uuid` | NOT NULL, FK → `conversations.id` (`ON DELETE CASCADE`) | Thread scoping (FR-010) |
| `sequence_number` | `bigint` | NOT NULL | Monotonically increasing per `conversation_id`; assigned atomically (see research.md #6) |
| `role` | `text` | NOT NULL, CHECK IN (`user`,`assistant`) | |
| `content` | `text` | NULL | User's question text, or the assistant's final generated answer text; NULL while `status` is `retrieving`/`generating` |
| `status` | `text` | NOT NULL, default `complete`, CHECK IN (`retrieving`,`generating`,`complete`,`failed`) | User messages are always `complete` immediately; assistant messages progress through this lifecycle |
| `failure_reason` | `text` | NULL | Set only when `status = 'failed'` (FR-016) |
| `is_grounded` | `boolean` | NOT NULL, default `true` | `false` when the message is an explicit "insufficient information" response (FR-005), so the frontend can render it distinctly |
| `created_at` | `timestamptz` | NOT NULL, default `now()` | |
| `updated_at` | `timestamptz` | NOT NULL, default `now()` | Updated as status progresses |

**Relationships**: Belongs to exactly one `conversations` row (thread), which belongs to
exactly one `projects` row. Has zero or more `message_citations` (assistant messages only).

**Validation rules**: `UNIQUE (conversation_id, sequence_number)` to guarantee strict,
gap-tolerant ordering per thread (FR-018).

**RLS policy**: Access requires `EXISTS (SELECT 1 FROM conversations JOIN projects ON
projects.id = conversations.project_id WHERE conversations.id = messages.conversation_id AND
projects.owner_id = auth.uid())`.

---

## Entity: `message_citations`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | `uuid` | PK, default `gen_random_uuid()` | |
| `message_id` | `uuid` | NOT NULL, FK → `messages.id` (`ON DELETE CASCADE`) | Only populated for assistant messages with `is_grounded = true` |
| `chunk_id` | `uuid` | NOT NULL, FK → `chunks.id` | The exact chunk that backed this part of the answer (FR-003, FR-004) |
| `document_id` | `uuid` | NOT NULL, FK → `documents.id` | Denormalized from `chunk_id` for direct query without an extra join |
| `asset_reference_id` | `uuid` | NULL, FK → `asset_references.id` | Present when the citing chunk was a table/image summary (FR-006, FR-007) |
| `created_at` | `timestamptz` | NOT NULL, default `now()` | |

**Relationships**: Belongs to exactly one `messages` row and references exactly one `chunks`
row (transitively one project, matching the citing message's own project via
`conversation_id`).

**Validation rules**: A given `(message_id, chunk_id)` pair MUST be unique — a chunk is cited
at most once per answer message, even if it contributed to multiple parts of the response.

**RLS policy**: Transitive via `message_id → messages.conversation_id → conversations.project_id
→ projects.owner_id = auth.uid()`.

---

## Cross-Cutting Rules

- `messages` and `message_citations` are additive; they fully realize the `Message` entity
  stub from 001-core-foundation without altering `conversations`, `projects`, or
  002-document-processing-pipeline's tables.
- Retrieval queries against `chunks` (via the LangChain/pgvector retriever) MUST always
  include a `project_id` filter matching the active conversation's project — this is enforced
  in the retriever construction (see research.md #1), not only via RLS, as defense-in-depth
  consistent with prior slices.
- A `message_citations` row referencing a `chunk_id` whose parent document has since been
  deleted should be handled gracefully at read time (citation shown as "source no longer
  available" per spec Edge Cases) rather than via a hard FK failure blocking display; the FK
  itself still enforces integrity at write time.
