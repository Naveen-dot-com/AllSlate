# Feature Specification: Document Processing Hardening

**Feature Branch**: `005-document-processing-hardening`

**Created**: 2026-08-17

**Status**: Draft

**Input**: User description: "Harden AllSlate's handling of non-ideal documents: scanned or image-only PDFs, documents with dense or irregular tables, and documents that mix languages or have poor scan quality. Every document type the app claims to support should produce a usable result — either a successfully processed document or a clearly explained failure — and the element/chunk inspection views from earlier should correctly reflect what OCR or table extraction actually found, including cases where extraction is partial or uncertain."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Every Supported Document Reaches a Usable Outcome (Priority: P1)

A user uploads any document of a type AllSlate claims to support — including difficult cases
like scanned pages, dense tables, mixed-language text, or poor scan quality — and the document
either finishes processing successfully and becomes usable, or clearly fails with an
understandable explanation. It never gets stuck, silently produces unusable content, or
appears successful while actually containing garbage or missing content.

**Why this priority**: This is the core trust guarantee of the hardening effort. Without it,
users cannot rely on AllSlate for real-world, imperfect documents — which are the norm, not
the exception, in most document collections.

**Independent Test**: Can be fully tested by uploading a batch of representative difficult
documents (scanned PDF, dense-table document, mixed-language document, poor-quality scan) and
confirming each one reaches either "stored" with genuinely usable content or "failed" with a
specific, understandable reason — with no document left stuck, silently degraded, or falsely
marked successful.

**Acceptance Scenarios**:

1. **Given** a scanned or image-only PDF with genuinely readable content, **When** it is
   uploaded, **Then** it reaches "stored" status with text that accurately reflects the
   document's actual content.
2. **Given** a scanned or image-only PDF whose content is illegible even after best-effort
   text recognition, **When** it is uploaded, **Then** it reaches "failed" status with a
   reason indicating the content could not be reliably extracted, rather than being marked
   "stored" with garbled or empty content.
3. **Given** a document containing dense or irregular tables (e.g., merged cells, multiple
   nested tables, tables spanning several pages), **When** it is uploaded, **Then** it either
   reaches "stored" with a usable representation of the table content, or "failed" with a
   reason specific to table extraction difficulty.
4. **Given** a document mixing multiple languages, **When** it is uploaded, **Then** it
   reaches "stored" with content correctly recognized across the languages present, or
   "failed" with a reason indicating a specific language could not be processed.
5. **Given** a poor-quality scan (e.g., low resolution, skewed, noisy background), **When** it
   is uploaded, **Then** the system makes a best-reasonable effort at extraction and either
   succeeds with usable content or fails with a reason describing the quality issue.

---

### User Story 2 - Inspection Views Accurately Reflect What Was Actually Extracted (Priority: P1)

A user viewing a processed document's element/chunk detail sees information that genuinely
matches what OCR or table extraction found — including being told explicitly when extraction
was partial, low-confidence, or uncertain — rather than a detail view that implies full
confidence or completeness when the underlying extraction was actually incomplete or shaky.

**Why this priority**: This directly extends the constitution's Retrieval Accuracy & Source
Fidelity principle. A confidently-presented but wrong or incomplete inspection view is worse
than no view at all, because it actively misleads users about what the system actually
"knows" from their document.

**Independent Test**: Can be fully tested by processing a document with a known
partially-extractable section (e.g., one unreadable page in an otherwise good scan) and
confirming the element/chunk detail view explicitly marks that section as partial/uncertain
rather than presenting it as if it were fully and confidently extracted.

**Acceptance Scenarios**:

1. **Given** a document where OCR successfully extracted some pages but not others, **When**
   the user views its element/chunk detail, **Then** the pages/elements that were not
   successfully extracted are clearly marked as such, distinct from successfully extracted
   ones.
2. **Given** a document with a table that was extracted with low confidence (e.g., an
   irregular table structure), **When** the user views that table element's detail, **Then**
   the view indicates the extraction is uncertain rather than presenting it with the same
   confidence as a cleanly extracted table.
3. **Given** a document that reached "stored" status despite one or more elements being
   partially or uncertainly extracted, **When** the user views the document's overall
   processing detail, **Then** the summary clearly indicates that the document is only
   partially or uncertainly represented, not fully and cleanly processed.
4. **Given** a document element extracted with full confidence, **When** the user views its
   detail, **Then** it is presented without any partial/uncertain indicator, so that such
   indicators remain meaningful signals rather than noise applied everywhere.

---

### User Story 3 - Clear, Specific Failure Reasons for Non-Ideal Documents (Priority: P2)

When a document ultimately fails to process, the user sees a failure reason specific enough
to understand what actually went wrong (e.g., "scanned pages 4–7 were unreadable" rather than
a generic "processing failed"), so they can decide whether to retry, replace, or abandon that
document.

**Why this priority**: This builds directly on the existing failure-reason requirement from
002-document-processing-pipeline, extending it specifically to the hardened set of
non-ideal-document failure modes. It matters most once the broader success/failure/partial
behaviors from Stories 1–2 exist.

**Independent Test**: Can be fully tested by intentionally uploading documents designed to
fail for different specific reasons (illegible scan, unsupported/unrecognized language,
severely malformed table) and confirming each produces a distinct, specific failure reason
rather than a single generic message.

**Acceptance Scenarios**:

1. **Given** a document that fails due to illegible scan quality, **When** the user views its
   failure reason, **Then** the reason specifically references scan/legibility quality, not a
   generic error.
2. **Given** a document that fails because a language present in it could not be processed,
   **When** the user views its failure reason, **Then** the reason specifically identifies the
   language issue.
3. **Given** a document that fails due to severely malformed table structure, **When** the
   user views its failure reason, **Then** the reason specifically references the table
   extraction difficulty.
4. **Given** two documents that fail for two different specific reasons, **When** the user
   compares their failure reasons, **Then** the reasons are distinguishable from one another,
   not identical generic text.

---

### Edge Cases

- What happens when a document is only partially in a supported language and partially in an
  unsupported one? The system must process the supported-language portions and clearly flag
  the unsupported portion rather than failing or silently dropping it.
- What happens when a table extraction produces a structurally plausible but factually
  incorrect table (e.g., misaligned columns) with no way for the system to detect the error
  automatically? The system should mark such extractions as uncertain whenever its confidence
  signals indicate irregularity, but this specification does not guarantee detection of every
  possible silent misextraction — see Assumptions.
- What happens when the same poor-quality scan is processed twice? The outcome (success,
  partial, or failure) should be consistent between runs, not randomly different.
- What happens if only a single page out of a large multi-page document is genuinely
  unreadable? The document should still be able to reach "stored" with that one page/section
  explicitly marked unreadable, rather than failing the entire document over one bad page,
  unless the unreadable portion is central enough to make the whole document unusable (see
  Assumptions for the threshold approach).
- What happens when a document type is uploaded that the system does not claim to support at
  all? This remains governed by the existing upload-validation behavior
  (002-document-processing-pipeline, FR-002); this hardening feature only concerns documents
  of claimed-supported types that are simply difficult examples of those types.
- How does the system prevent a partially/uncertainly extracted document from silently
  contributing unreliable, uncited-as-uncertain content to chat answers
  (003-rag-project-chat)? Retrieval and citation display must be able to reflect the
  same partial/uncertain markers established here.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: For every document type AllSlate claims to support, the system MUST produce
  either a "stored" document with genuinely usable extracted content, or a "failed" document
  with a specific, understandable failure reason — never an indefinite stuck state.
- **FR-002**: The system MUST NOT mark a document "stored" when its extracted content is
  empty, entirely illegible, or otherwise not usable as a source for answering questions.
- **FR-003**: When OCR produces genuinely readable text (even if scan quality was poor), the
  system MUST proceed with that text through the remaining pipeline stages rather than
  failing solely because the source was a scan.
- **FR-004**: When OCR cannot produce usable text for a document or a significant portion of
  it, the system MUST mark the affected document or section as failed/unreadable with a
  specific reason, consistent with the OCR failure handling established in
  002-document-processing-pipeline.
- **FR-005**: The system MUST support extraction of dense or irregular table structures (e.g.,
  merged cells, multi-page tables) to the best extent technically feasible, producing a usable
  table representation and/or summary when extraction succeeds.
- **FR-006**: When table extraction cannot produce a reliable result for a given table, the
  system MUST mark that table element as failed or uncertain rather than presenting a
  fabricated or silently wrong structure with full confidence.
- **FR-007**: The system MUST correctly recognize and process text across multiple languages
  present within the same document, to the extent those languages are supported.
- **FR-008**: When a document contains a language the system cannot process, the system MUST
  process the supported-language portions and clearly flag the unsupported-language portion,
  rather than failing the entire document or silently omitting the affected content without
  indication.
- **FR-009**: The system MUST track, per element, whether its extraction was fully confident,
  partial, or uncertain, and MUST make this distinction visible in the element/chunk
  inspection views.
- **FR-010**: The system MUST NOT present a partially or uncertainly extracted element in the
  inspection views with the same visual/informational confidence as a fully and cleanly
  extracted element.
- **FR-011**: When a document reaches "stored" status despite containing one or more partial
  or uncertain elements, the system MUST clearly indicate at the document level that the
  document is only partially or uncertainly represented, not fully and cleanly processed.
- **FR-012**: The system MUST allow a document to reach "stored" status with some
  individual elements marked unreadable/uncertain, provided enough of the document was usably
  extracted overall, rather than failing the entire document over an isolated bad section.
- **FR-013**: The system MUST fail an entire document (rather than storing it with only
  isolated partial content) when the unreadable or uncertain portion is extensive enough that
  the resulting stored content would not be meaningfully usable as a source.
- **FR-014**: Every failure reason produced under this hardening effort MUST be specific to
  its actual cause (e.g., scan legibility, unsupported language, malformed table structure),
  and distinguishable from other failure reasons, rather than a single generic error message.
- **FR-015**: Partial/uncertain markers established at the element level MUST be available to
  retrieval and citation display (003-rag-project-chat) so that chat answers can reflect when
  their supporting source material was only partially or uncertainly extracted.
- **FR-016**: The processing outcome (stored, partial-stored, or failed, and the specific
  reason if failed) for a given document MUST be consistent across repeated processing
  attempts of the same input, absent any change to the document itself.

### Key Entities

- **Extraction Confidence Marker**: An indicator attached to an element (and rolled up to its
  document) describing whether its extraction was fully confident, partial, or uncertain,
  along with a human-readable note on why (e.g., "low scan quality," "irregular table
  structure," "unsupported language segment"). Extends the `Element` entity from
  002-document-processing-pipeline.
- **Document Processing Outcome**: The overall result of a document's processing —
  successfully and fully stored, stored-with-partial-content, or failed — along with a
  specific reason when not fully successful. Extends the `Document` entity's status/failure
  reason from 002-document-processing-pipeline.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of uploaded documents of a claimed-supported type reach either "stored"
  (fully or partially) or "failed" with a specific reason — 0 documents left indefinitely
  stuck or silently degraded, across hardening test suites covering scanned, dense-table,
  mixed-language, and poor-quality-scan documents.
- **SC-002**: 0 instances, across testing, of a document reaching "stored" status with content
  that is empty, entirely illegible, or otherwise unusable as a retrieval source.
- **SC-003**: 100% of partially or uncertainly extracted elements are visibly marked as such in
  the inspection view, verified across a test set of documents with known partial/uncertain
  sections.
- **SC-004**: 100% of documents with at least one partial/uncertain element also show a
  document-level partial/uncertain indicator, with 0 false negatives in testing.
- **SC-005**: In testing, at least 90% of failure reasons produced for the four hardened
  difficult-document categories (illegible scan, unreadable OCR portion, malformed table,
  unsupported language segment) are judged by reviewers to be specific and actionable, not
  generic.
- **SC-006**: Reprocessing the same difficult document under unchanged conditions produces the
  same outcome (stored/partial/failed and, if failed, the same reason category) in 100% of
  repeated-run tests.

## Assumptions

- This feature builds on 002-document-processing-pipeline (pipeline stages, element/chunk
  model, status/failure-reason model) and 003-rag-project-chat (retrieval/citations); it
  extends their behavior for difficult documents rather than replacing the core pipeline
  design.
- The exact technical confidence-scoring mechanism (e.g., an OCR engine's own confidence
  score, or heuristics on table structure regularity) is an implementation detail; this
  specification only requires that some meaningful confidence/partial signal exists and is
  surfaced consistently, not a specific scoring algorithm.
- The threshold for "isolated bad section, still store the rest" versus "too much bad content,
  fail the whole document" (FR-012 vs. FR-013) is a tunable implementation parameter; this
  specification requires the behavior/distinction to exist, not a specific numeric cutoff.
- "Supported languages" refers to whatever set of languages the underlying OCR/text-processing
  capability is configured to support at implementation time; this specification does not
  mandate universal language coverage, only correct, explicit handling of the configured
  boundary.
- Detecting every possible silent table-misextraction (e.g., a plausible-looking but factually
  wrong table) is not guaranteed; this specification requires the system to flag extractions
  its own confidence signals indicate as irregular, not to achieve perfect error detection.
- No new user-facing retry/reprocess action is introduced by this specification (consistent
  with 002-document-processing-pipeline's existing assumption that retry/reprocess is a future
  feature); hardening here concerns processing correctness and inspection-view accuracy for a
  single processing attempt.
