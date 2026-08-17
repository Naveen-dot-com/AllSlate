# Phase 0 Research: Document Processing Hardening

## 1. Sourcing OCR/Extraction Confidence Signals

**Decision**: Use the confidence scores already available from the OCR engine underlying
Unstructured's partitioning (per-page and, where available, per-text-block confidence), plus a
structural-regularity heuristic for tables (e.g., consistent column counts across rows, no
unexpected merged-cell artifacts) to compute a per-element confidence classification:
`confident`, `partial`, or `uncertain`. A page/element falls below `confident` when its OCR
confidence score is under a configured threshold, or when table-structure checks flag
irregularity.

**Rationale**: The spec (FR-009) requires the distinction to exist and be visible, but
explicitly treats the scoring mechanism as an implementation detail (Assumptions). Reusing
signals the OCR engine and Unstructured already compute avoids introducing a separate,
redundant analysis pass (Principle IV), keeping this a hardening change rather than a new
subsystem.

**Alternatives considered**: Building a custom ML confidence model — rejected as
disproportionate scope for a hardening slice; the spec only requires "some meaningful
confidence/partial signal," not a novel scoring algorithm.

## 2. Document-Level Rollup of Element Confidence

**Decision**: A document's overall outcome is computed as: `stored` (all elements confident),
`stored_partial` (at least one element partial/uncertain, but overall usable content
sufficient — see decision #3 for the threshold approach), or `failed` (unusable overall). The
document-level rollup is derived, not independently set, from its elements' confidence
markers plus the partial-vs-fail threshold.

**Rationale**: Directly implements FR-011 (document-level indicator must reflect element-level
issues) while keeping a single source of truth (element confidence) that rolls up rather than
requiring separate, potentially inconsistent bookkeeping (Principle III: observability
requires consistency between component and aggregate views).

**Alternatives considered**: Manually/independently flagging document-level partial status —
rejected, risks the document-level flag drifting out of sync with actual element-level
findings.

## 3. Partial-vs-Fail Threshold

**Decision**: Configure a threshold (e.g., percentage of pages/elements that are
uncertain/unreadable) below which a document proceeds to `stored_partial`, and above which the
entire document is marked `failed`. The exact numeric threshold is a tunable configuration
value, not hardcoded inline, so it can be adjusted operationally without a code change.

**Rationale**: The spec (FR-012/FR-013, Assumptions) explicitly requires the
isolated-bad-section-vs-fail-everything distinction to exist, while leaving the exact cutoff
as an implementation detail. A configuration value (rather than a hardcoded constant) supports
future tuning based on real-world results without needing a redeploy of pipeline logic itself.

**Alternatives considered**: A hardcoded, non-configurable threshold — rejected as less
flexible; given this is explicitly called out as tunable in the spec's Assumptions, a
configuration value is the more appropriate fit.

## 4. Explicit LangGraph Error Edges for Partition/OCR Failures

**Decision**: Add explicit conditional edges from the `ocr` and `partition` nodes (established
in 002-document-processing-pipeline) that catch node-level exceptions and low-confidence/
unreadable-threshold breaches, mapping each distinct cause to a specific `failed`-status reason
via a shared `errors.py` mapping module, then transition the graph to the terminal `failed`
node. Every other node in the graph already has (per 002's plan) a catch-all error transition;
this slice makes the `ocr`/`partition` cases specific rather than falling through to a generic
"unhandled exception" state.

**Rationale**: Directly implements FR-001, FR-004, FR-014: every partition/OCR problem must
resolve to the pipeline's existing `failed` status with a specific reason, never an unhandled
exception that could crash the worker or leave the document status stuck (violating
constitution Principle VII).

**Alternatives considered**: A single generic catch-all "processing error" reason for all
partition/OCR failures — rejected, conflicts with FR-014's requirement that failure reasons be
specific and distinguishable per actual cause.

## 5. Multi-Language Handling

**Decision**: Configure the OCR/partitioning step with the project's supported language set
(a fixed, implementation-level configuration per Assumptions); when a document contains
segments in an unsupported language, those segments are flagged with an
`unsupported_language_segment` confidence reason (following decision #1's classification
scheme) rather than causing a full document failure, consistent with FR-008.

**Rationale**: Directly implements FR-007/FR-008: supported-language portions must still
process normally, and unsupported segments must be explicitly flagged rather than silently
dropped or causing full failure.

**Alternatives considered**: Failing the entire document if any unsupported language segment
is detected — rejected, explicitly conflicts with FR-008's requirement to process the
supported portions and flag only the unsupported one.

## 6. Reprocessing Determinism

**Decision**: Confidence computation and error-edge routing are made purely a function of the
document's content and the fixed OCR/partitioning configuration (no randomness, no
time-based or environment-dependent branching), so that reprocessing the same input under
unchanged configuration produces the same outcome and reason category (FR-016). Where the
underlying OCR engine has any inherent non-determinism (e.g., multi-threaded processing
producing slightly different confidence scores across runs), the confidence classification
uses threshold buckets (`confident`/`partial`/`uncertain`) rather than raw scores for the
outcome decision, absorbing small score fluctuations without changing the resulting bucket in
typical cases.

**Rationale**: Directly implements FR-016 and SC-006; bucketing rather than comparing raw
scores directly reduces flakiness in tests and in production behavior.

**Alternatives considered**: Comparing raw confidence scores directly against a hard cutoff
with no bucketing tolerance — rejected as more prone to flaky/inconsistent outcomes across
repeated runs of borderline-confidence documents.

## 7. Hardening Test Fixture Suite

**Decision**: Add a `tests/fixtures/hardening/` directory containing: a scanned/image-only
PDF with genuinely readable content, a scanned PDF with an illegible page, a multi-language PDF
(mixing a supported and an intentionally-unsupported language), a dense/irregular-table PDF
(merged cells, multi-page table), and a poor-quality-scan PDF (low resolution/skew/noise).
Each fixture is exercised by an integration test asserting the expected final status
(`stored`, `stored_partial`, or `failed`), the expected confidence markers, and — for failures
— a reason matching the expected specific category.

**Rationale**: Directly fulfills the explicit instruction to add test documents covering
scanned PDFs, multi-language pages, and complex tables, and gives concrete, repeatable
coverage for every hardening behavior described in the spec.

**Alternatives considered**: Relying only on unit tests with mocked OCR/partitioning output —
rejected as insufficient on its own; real (or realistic synthetic) fixture documents are needed
to validate actual end-to-end behavior of the hardening logic against genuine difficult inputs.
