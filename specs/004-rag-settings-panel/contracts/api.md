# API Contract: RAG Settings Panel

All endpoints require a valid Supabase JWT and are scoped under an owned project + owned
conversation thread. Requests referencing a project/thread the caller does not own receive
`404 Not Found` (never `403`), consistent with prior slices.

## GET /api/v1/projects/{project_id}/conversations/{conversation_id}/settings

Retrieve the current settings for a conversation thread (creating defaults if none exist yet).

**Responses**:
- `200 OK` — `{ "web_search_enabled", "creativity_level", "retrieval_top_k",
  "included_document_types", "updated_at" }`.
- `404 Not Found` — conversation/project not found or not owned by caller.
- `401 Unauthorized` — missing/invalid JWT.

---

## PATCH /api/v1/projects/{project_id}/conversations/{conversation_id}/settings

Update one or more settings fields for a conversation thread. Applies immediately to the next
`ask` call in this thread (FR-012); does not affect any answer already generating (FR-013) or
any previously delivered answer (FR-014).

**Request body** (all fields optional, partial update):
```json
{
  "web_search_enabled": true,
  "creativity_level": "creative",
  "retrieval_top_k": 12,
  "included_document_types": ["text", "table"]
}
```

**Responses**:
- `200 OK` — the full updated settings object.
- `422 Unprocessable Entity` — validation error, including:
  - `included_document_types` is an empty array (FR-011).
  - `retrieval_top_k` out of allowed range.
  - `creativity_level` not one of the allowed plain-language values.
- `404 Not Found` — conversation/project not found or not owned by caller.
- `401 Unauthorized` — missing/invalid JWT.

---

## Interaction with POST .../ask (003-rag-project-chat, unchanged endpoint shape)

No new request fields are added to the existing `ask` endpoint's request body. Instead, the
backend reads `conversation_settings` for the target `conversation_id` at the start of
handling each `ask` call and uses the resolved values to configure retrieval (`retrieval_top_k`,
`included_document_types`), the web-search routing node (`web_search_enabled`), and generation
(`creativity_level` → `temperature`). The `complete` SSE event's citation list MAY include
entries with a `source_type: "web"` in addition to the existing project-document citation
shape, when web search contributed to the answer.

---

## Cross-Cutting Contract Rules

- Every settings read/write MUST be validated against the authenticated caller's ownership of
  both the project and the conversation thread, reusing the `get_owned_conversation` dependency
  from 003-rag-project-chat.
- A settings change MUST take effect only for `ask` calls submitted after the change persists
  successfully — never retroactively for an in-flight or already-completed answer.
- No settings response may ever reveal or be influenced by another user's or project's
  conversation settings.
