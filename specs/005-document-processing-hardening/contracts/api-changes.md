# API Contract Changes: Document Processing Hardening

No new endpoints are introduced. This feature extends the response shape of existing
endpoints from 002-document-processing-pipeline to surface confidence and specific failure
categories. All existing authentication, ownership, and isolation contract rules from
002-document-processing-pipeline remain unchanged and apply identically here.

## GET /api/v1/projects/{project_id}/documents/{document_id} (extended)

**Response additions**:
- `status` may now be `stored_partial` in addition to the existing values.
- `failure_category` (nullable) — one of `illegible_scan`, `unreadable_ocr_portion`,
  `malformed_table`, `unsupported_language`, `other`; present when `status = 'failed'`.
- `has_low_confidence_content` (boolean, derived) — `true` when `status = 'stored_partial'`,
  provided as a convenience flag so the frontend doesn't need to infer it from `status` string
  matching alone.

---

## GET /api/v1/projects/{project_id}/documents/{document_id}/elements (extended)

**Response additions per element**:
- `confidence` — `confident` | `partial` | `uncertain`.
- `confidence_reason` (nullable) — human-readable explanation, present when `confidence !=
  'confident'`.

---

## Cross-Cutting Contract Rules

- All existing ownership/authorization rules from 002-document-processing-pipeline's contract
  (404 on unowned project/document, 401 on missing/invalid JWT) apply unchanged to these
  extended responses.
- Adding `stored_partial` as a new possible `status` value and adding new optional response
  fields is additive and backward-compatible with any existing consumer that only checks for
  `status == 'stored'` as a boolean-ish success signal; however, frontend code MUST be updated
  (per plan.md) to treat `stored_partial` as a successful-but-flagged outcome, not as a failure.
