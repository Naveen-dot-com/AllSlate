# Data Model: RAG Settings Panel

This feature adds one new table and one denormalized snapshot field on the existing
`messages` table (003-rag-project-chat). It reads (but does not modify) `conversations`
(001-core-foundation) and the document-type taxonomy established in
002-document-processing-pipeline.

## Entity: `conversation_settings`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `conversation_id` | `uuid` | PK, FK → `conversations.id` (`ON DELETE CASCADE`) | 1:1 with a conversation thread |
| `web_search_enabled` | `boolean` | NOT NULL, default `false` | FR-004; off by default |
| `creativity_level` | `text` | NOT NULL, default `'balanced'`, CHECK IN (`'precise'`,`'balanced'`,`'creative'`) | Plain-language control (FR-007); maps to `temperature` internally |
| `retrieval_top_k` | `int` | NOT NULL, default `8`, CHECK (`retrieval_top_k` BETWEEN 1 AND 50) | FR-009; bounded to a sane range |
| `included_document_types` | `text[]` | NOT NULL, default `'{all}'` (sentinel meaning "all known types") | FR-010; MUST NOT be empty (FR-011, enforced at write time) |
| `updated_at` | `timestamptz` | NOT NULL, default `now()` | Updated on every change |

**Relationships**: Belongs to exactly one `conversations` row (transitively one project).

**Validation rules**: `included_document_types` MUST contain at least one entry (or the `all`
sentinel) — rejected at the API layer before persistence (FR-011).

**RLS policy**: Access requires `EXISTS (SELECT 1 FROM conversations JOIN projects ON
projects.id = conversations.project_id WHERE conversations.id =
conversation_settings.conversation_id AND projects.owner_id = auth.uid())` — same transitive
pattern as `messages` in 003-rag-project-chat.

---

## Extension: `messages.effective_settings_snapshot` (003-rag-project-chat)

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `effective_settings_snapshot` | `jsonb` | NULL | Populated on assistant messages only: the resolved `conversation_settings` values in effect when this specific question was submitted (FR-013) |

**Rationale**: Recording the snapshot per-message (rather than only referencing the live
`conversation_settings` row) preserves an accurate audit/observability record even after the
conversation's settings later change (constitution Principle III/VIII), and makes FR-013's
"in-flight generation unaffected by later changes" behavior independently verifiable per
message.

---

## Cross-Cutting Rules

- `conversation_settings` is created with defaults automatically when a conversation thread is
  created (or lazily on first `GET`), so every thread always has a well-defined settings row —
  no thread is ever missing settings or falls back to undocumented implicit defaults.
- The `ask` endpoint (003-rag-project-chat) reads `conversation_settings` exactly once per
  question, at submission time, and uses that snapshot for both the web-search routing
  decision and generation parameters — never re-reading mid-flight (see research.md #6).
- `included_document_types` values correspond to the element/document type categories already
  established in 002-document-processing-pipeline; this feature does not define a new taxonomy.
