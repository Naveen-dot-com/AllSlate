# Data Model: Document Processing Hardening

This feature adds columns to two existing tables from 002-document-processing-pipeline. No
new tables are introduced.

## Extension: `elements` (002-document-processing-pipeline)

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `confidence` | `text` | NOT NULL, default `'confident'`, CHECK IN (`'confident'`,`'partial'`,`'uncertain'`) | FR-009 |
| `confidence_reason` | `text` | NULL | Human-readable note (e.g., "low OCR confidence on page 4," "irregular table structure," "unsupported language segment"); populated whenever `confidence != 'confident'` |

**Validation rules**: `confidence_reason` MUST be non-null whenever `confidence` is `partial`
or `uncertain` (FR-009's "visible" requirement implies a reason must accompany the marker, not
just a bare flag).

**RLS policy**: Unchanged — inherits `elements`' existing transitive project-ownership policy
from 002-document-processing-pipeline.

---

## Extension: `documents` (002-document-processing-pipeline)

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `status` | `text` | (existing CHECK, extended) now additionally allows `'stored_partial'` | Rolled up from element confidence per research.md #2; distinct from plain `'stored'` so the UI can show a document-level partial/uncertain indicator (FR-011) |
| `failure_category` | `text` | NULL, CHECK IN (`'illegible_scan'`,`'unreadable_ocr_portion'`,`'malformed_table'`,`'unsupported_language'`, `'other'`) | Populated only when `status = 'failed'`; used alongside the existing free-text `failure_reason` to guarantee distinguishable, specific categories (FR-014) |

**Validation rules**: `failure_category` MUST be set whenever `status = 'failed'` and the
failure originated from partition/OCR (per the explicit LangGraph error edges in research.md
#4); `status = 'stored_partial'` MUST correspond to at least one associated `elements` row with
`confidence != 'confident'`.

**RLS policy**: Unchanged — inherits `documents`' existing transitive project-ownership policy.

---

## Cross-Cutting Rules

- `status = 'stored_partial'` is a refinement of the existing `'stored'` outcome, not a new
  pipeline stage; the LangGraph flow's node sequence (uploaded → queued → partitioning →
  chunking → summarizing → vectorizing → stored) is unchanged — only the final resolved status
  value gains this additional nuance.
- `failure_category` is additive to (not a replacement for) the existing free-text
  `failure_reason` column from 002-document-processing-pipeline; both are populated together
  on failure so existing consumers of `failure_reason` continue to work unmodified.
- Retrieval/citation display (003-rag-project-chat) MAY read `elements.confidence` /
  `confidence_reason` via the existing `chunks → elements` relationship to surface
  partial/uncertain markers on citations (FR-015); this plan does not require modifying the
  `chunks` or `message_citations` schema itself, since the confidence data is reachable via the
  existing `chunks.element_id` foreign key.
