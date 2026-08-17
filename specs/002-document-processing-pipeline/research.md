# Phase 0 Research: Document Processing Pipeline

## 1. Pipeline Orchestration with LangGraph

**Decision**: Model the pipeline as a LangGraph `StateGraph` with one node per stage:
`queued → partition → chunk → summarize → vectorize → stored`, plus a conditional `ocr` node
inserted before `partition` when the document is detected as image-only/scanned, and a
terminal `failed` node reachable from any node via error edges. The graph's shared state
object carries the document id, project id, accumulated elements/chunks, and an error field.

**Rationale**: The spec's visible statuses map directly to graph nodes, so persisting "current
node" as the document's status satisfies FR-003/FR-004 without inventing a separate status
enum disconnected from execution. LangGraph's conditional edges cleanly express the
OCR-only-when-needed branch (FR-012) and the "any stage can fail" requirement (FR-004) via a
catch-all error transition per node.

**Alternatives considered**: A hand-rolled state machine (enum + switch statement) — rejected,
since LangGraph already provides checkpointing/resumability primitives that reduce custom code
for a multi-stage async workflow (Principle IV: avoid duplicated logic).

## 2. Async Execution Mechanism

**Decision**: Run the LangGraph pipeline in a dedicated background worker process (e.g., an
async worker consuming from a lightweight queue) rather than FastAPI's in-process
`BackgroundTasks`, so that pipeline execution survives web-process restarts/deploys and scales
independently of API request load. Upload endpoint only persists the document row (status
`uploaded`→`queued`) and enqueues a job; it does not run any pipeline node inline.

**Rationale**: FR-006/FR-022 require that processing continues even if a user navigates away
and never blocks the UI; a queue/worker split guarantees the API request returns in <2s
(SC-007) regardless of document complexity and isolates pipeline crashes from the web tier.

**Alternatives considered**: `FastAPI BackgroundTasks` — rejected as the primary mechanism
because tasks run in the same process/lifecycle as the web server, so a server restart or
crash would silently drop or corrupt in-flight processing, risking FR-022's "must continue
even if..." and Principle VII's "must not leave documents in ambiguous states."

## 3. Partitioning & Chunking with Unstructured

**Decision**: Use the `unstructured` library's partitioning to produce typed elements (Title,
NarrativeText/Text, Table, Image, and other native categories), then apply its "chunk by
title" strategy so chunks respect section boundaries rather than fixed-size windows.

**Rationale**: Directly satisfies FR-009 ("preserve original structure... associating content
with its originating section") and constitution Principle II (source fidelity); chunk-by-title
is a built-in strategy purpose-built for this structural-alignment requirement, avoiding a
custom chunker.

**Alternatives considered**: Fixed-size/character-count chunking — rejected, since it can
split content mid-section and would violate the structural-fidelity requirement.

## 4. OCR for Image-Only / Scanned Documents

**Decision**: Before partitioning, detect image-only/scanned documents (e.g., PDFs with no
extractable text layer, or raw image uploads) and run an explicit OCR node that produces a
text layer, which is then fed into the same partitioning step as any other document.
Unstructured's OCR-capable partitioning strategy (or an underlying OCR engine it delegates to)
is used so OCR output flows into the same typed-element model rather than a separate code path.

**Rationale**: FR-012 requires OCR as an explicit, separately visible pipeline step (i.e., a
distinct status/graph node), and FR-013 requires marking the document failed when OCR yields no
usable text — both map cleanly onto a dedicated LangGraph `ocr` node with a conditional edge
that routes to `failed` when extracted text is empty/below a usability threshold.

**Alternatives considered**: Silently attempting normal partitioning first and only falling
back to OCR on failure — rejected, since the spec explicitly requires OCR to be a *visible*
status the user can observe (FR-012), not an invisible fallback.

## 5. Multimodal Summarization for Tables/Images

**Decision**: For every `Table` and `Image` element, call Gemini's multimodal API to generate a
text summary, storing the summary text linked to a new `AssetReference` row pointing at the
original table/image asset persisted in Supabase Storage. Summarization failures are retried
with bounded backoff before the document is marked `failed` at the `summarizing` stage with a
specific reason.

**Rationale**: Directly implements FR-010/FR-011 and the edge case requiring retry-then-fail
behavior (not silent skipping) per constitution Principle VII. Keeping the original asset in
Storage (rather than only its summary) satisfies the "redisplayed... alongside summary"
requirement (FR-011, User Story 3 acceptance scenario 2).

**Alternatives considered**: Skipping unsummarizable tables/images silently — rejected, since
the spec explicitly forbids silently producing chunks with missing summary data.

## 6. Chunk Representation & Embedding Storage

**Decision**: Represent every final chunk as a LangChain `Document` object: `page_content` is
either the raw element text (text/title elements) or the generated summary (table/image
elements); `metadata` carries `document_id`, `element_type`, `asset_reference_id` (nullable),
`page_number`, and `processed_at`. Chunks are embedded and stored in a Postgres `chunks` table
using the `pgvector` extension, with the same metadata columns persisted alongside the vector
(not only inside an opaque JSON blob) so they can be filtered/queried directly.

**Rationale**: This is an explicit instruction from the user and directly satisfies FR-014/FR-015
and constitution Principle II (every answer traceable to exact source chunk). Persisting
metadata as real columns (not just embedded in vector-store payload) satisfies FR-016/FR-017's
requirement that detail views be queried directly rather than re-parsed.

**Alternatives considered**: Storing only the LangChain `Document`'s metadata as an opaque JSON
column — rejected for querying convenience, since FR-016/FR-018 require direct queryability for
the status-detail view without re-parsing.

## 7. Persisted Status Tracking & Detail Queries

**Decision**: Every LangGraph node transition writes a `processing_status_events` row
(document_id, stage, started_at/occurred_at, and — for `failed` — a reason). The document's
"current status" is derived as the latest event for that document, so reload recovery (FR-008,
FR-023) is a simple query rather than requiring in-memory state. Per-document element counts
and per-element metadata are persisted in `elements` (and summaries/asset references linked to
them) as each partitioning/summarization step completes, satisfying FR-016–FR-018 without
re-parsing.

**Rationale**: Matches constitution Principle III's requirement that every stage be "observable
and queryable" with "meaningful status, timestamps, progress, and errors," and directly
supports the reload-recovery scenarios in User Story 2.

**Alternatives considered**: Keeping status only in an in-memory job-queue/worker state —
rejected, since it would not survive reloads or worker restarts, violating FR-008/FR-023.

## 8. Live Status Delivery (SSE vs. WebSocket)

**Decision**: Use Server-Sent Events (SSE) for the status stream: the frontend opens a
one-way `EventSource` connection per open project (or per document), and the backend publishes
an event whenever a `processing_status_events` row is inserted for a document in that project.
On initial connection (and on reconnect after a drop), the endpoint first emits the current
status of all in-flight documents (from the persisted event table) before streaming further
updates, so reconnect/reload always recovers accurate state (FR-023).

**Rationale**: Status updates are strictly server-to-client (no client-to-server messages
needed for this feature), making SSE simpler to implement and operate than a full-duplex
WebSocket, while still satisfying the "no polling" requirement (FR-007). SSE also degrades
gracefully (auto-reconnect is a native browser `EventSource` behavior), directly helping the
"real-time delivery interruption" edge case.

**Alternatives considered**: WebSocket — viable and not rejected outright (the user's request
allows either); SSE is chosen for this slice due to lower operational complexity for a
one-directional status feed. If future features need bidirectional streaming (e.g., live chat
tokens), WebSocket can be introduced separately without conflicting with this decision.

## 9. Project Isolation for New Tables

**Decision**: Apply the same RLS pattern established in 001-core-foundation to all new tables
(`documents`, `processing_status_events`, `elements`, `chunks`, `asset_references`,
`summaries`): each row is scoped (directly or transitively) to a `project_id` whose owning
project's `owner_id` must equal `auth.uid()`. Supabase Storage paths for original documents and
extracted assets are namespaced by `project_id` (e.g.,
`{project_id}/documents/{document_id}/...`) so storage-level access can also be scoped per
project via Storage policies.

**Rationale**: Directly satisfies FR-019–FR-021 and constitution Principle I's requirement for
database-layer enforcement in addition to API-layer checks, extending rather than duplicating
the existing isolation model.

**Alternatives considered**: Reusing a single shared storage bucket path without project
namespacing — rejected, since it would rely entirely on database records (not storage-layer
structure) for isolation, weakening defense-in-depth.
