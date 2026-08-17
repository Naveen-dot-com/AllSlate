# Phase 0 Research: RAG Project Chat

## 1. Project-Scoped Similarity Search with LangChain

**Decision**: Build a LangChain retriever backed by a `PGVector` (or equivalent pgvector
integration) vector store, configured with a mandatory metadata filter on `project_id` applied
at the database query level (not post-filtered in application code after retrieval). The
question is embedded with the same embedding model used at ingestion time
(002-document-processing-pipeline), and similarity search runs only against rows already
scoped to the active project.

**Rationale**: Constitution Principle I requires isolation enforced at "every application and
database layer"; filtering at the SQL/query level (rather than fetching top-k globally and
discarding cross-project results afterward) guarantees no cross-project chunk is ever loaded
into application memory or considered for ranking, which is both a stronger security posture
and avoids skewing top-k results with irrelevant projects' content.

**Alternatives considered**: Retrieve top-k globally then filter by project in Python —
rejected, since it both risks momentarily handling another project's data in memory and can
return fewer than k relevant results for the active project if other projects' chunks rank
higher globally.

## 2. Assembling Retrieved Documents into Gemini Context

**Decision**: Retrieved LangChain `Document`s (each with `page_content` + metadata from
002-document-processing-pipeline: `document_id`, `element_type`, `page_number`,
`asset_reference_id`, `processed_at`) are assembled into a structured prompt context where
each snippet is clearly delimited and tagged with a citation index/id. Gemini is instructed
(via system/prompt design) to answer only using the provided context and to reference which
snippet(s) it used, which the backend then maps back to full citation metadata rather than
trusting free-text citation claims verbatim.

**Rationale**: FR-002/FR-003 require grounded answers with verifiable citations; explicitly
delimiting and indexing context snippets lets the backend authoritatively determine which
chunks "backed" the answer (for persistence and table/image attachment) rather than relying
solely on the model's self-reported citations, which could be inaccurate.

**Alternatives considered**: Trusting the model's free-text citation output as the source of
truth — rejected, since it could hallucinate a citation that doesn't correspond to an actual
retrieved chunk, undermining Principle II's traceability guarantee.

## 3. Table/Image Attachment to Responses

**Decision**: After the backend determines which retrieved chunks contributed to the answer
(per decision #2), for every contributing chunk whose metadata includes a non-null
`asset_reference_id`, the backend resolves that reference to a Supabase Storage URL (reusing
the asset-reference resolution pattern from 002-document-processing-pipeline) and attaches it
to the response payload alongside the answer text and citation list.

**Rationale**: Directly implements FR-006–FR-008: the original table/image, not just its
summary text, must be shown. Reusing the existing asset-reference resolution avoids
duplicating storage-access logic (Principle IV).

**Alternatives considered**: Re-fetching/re-rendering the table/image from the source document
at answer time — rejected as redundant and slower; the already-extracted, already-stored asset
from ingestion is the correct, faster source per Principle V.

## 4. Streaming Responses via SSE

**Decision**: Reuse the SSE pattern established for processing-status streaming
(002-document-processing-pipeline) for chat: the ask-question endpoint opens an SSE stream
that first emits a `retrieving` phase event, then a `generating` phase event once retrieval
completes, then a sequence of token/partial-answer events, and finally a `complete` event
carrying the final answer, citations, and any table/image attachments (or a `failed` event on
error).

**Rationale**: FR-014 requires distinct retrieving vs. generating indicators in real time;
SSE (already adopted for status streaming) keeps the two streaming use cases in the codebase
consistent (Principle IV: avoid duplicated/inconsistent patterns) and requires no
bidirectional client-to-server messaging for this feature.

**Alternatives considered**: WebSocket — not rejected outright, but SSE is chosen for
consistency with the existing status-stream implementation and because chat responses in this
slice are still fundamentally one-directional (question submitted via a regular POST/request,
then a one-way stream of the answer).

## 5. Persisting Messages and Backing Citations

**Decision**: Persist every user question and system answer as a row in a `messages` table
(extending the `messages` entity referenced in 001-core-foundation's data model, now fully
implemented here), including a `status` field (`retrieving`/`generating`/`complete`/`failed`)
and a `failure_reason` for failed answers. For each answer message, persist one row per
contributing chunk in a `message_citations` table, linking the message to the specific
`chunks.id` it was grounded in (reusing 002-document-processing-pipeline's traceability
metadata directly rather than duplicating it).

**Rationale**: FR-016 requires failures to be surfaced without corrupting history — a
persisted `status`/`failure_reason` on the message row itself achieves this cleanly. Storing
per-citation rows (rather than a JSON blob) keeps citations directly queryable, consistent
with 002-document-processing-pipeline's precedent of persisting structured, queryable metadata
rather than opaque blobs.

**Alternatives considered**: Storing citations as an embedded JSON array on the message row —
rejected for consistency with the existing structured-metadata approach and to allow querying
"which messages cited chunk X" if ever needed (e.g., future dependent-answer invalidation).

## 6. Concurrency-Safe Message Ordering

**Decision**: Each message row has a strictly increasing `sequence_number` scoped to its
thread (assigned atomically, e.g., via a database sequence or a serializable insert with
thread-scoped locking), so that even if a user sends a new message before a prior answer
finishes, both messages are correctly ordered and neither is lost or duplicated. The
in-progress answer for the prior message continues generating independently and is written to
its own row when complete, regardless of newer messages arriving in the same thread meanwhile.

**Rationale**: Directly implements FR-018 and FR-019 (background completion tied to originating
thread) and the corresponding edge cases; a per-thread monotonic sequence avoids relying purely
on wall-clock timestamps, which can collide or arrive out of order under concurrent writes.

**Alternatives considered**: Relying solely on `created_at` timestamps for ordering — rejected,
since concurrent inserts could have colliding or out-of-order timestamps depending on clock
resolution and transaction commit order.

## 7. Handling Insufficient Evidence

**Decision**: If the similarity search returns no chunks above a minimum relevance threshold
(or returns zero chunks, e.g., an empty/newly created project), the backend skips the
generation call entirely and returns a `complete` message with a fixed "insufficient
information" response type (a distinct, explicit status rather than a normal generated answer)
so the frontend can render it distinctly and it is never confused with a real, cited answer.

**Rationale**: FR-005 explicitly requires this to be a clear, distinct indication rather than a
guess; skipping generation when there's no retrieved context also avoids Gemini being tempted
to answer from general knowledge, directly protecting Principle II (no hallucination/unsupported
claims).

**Alternatives considered**: Always calling Gemini and instructing it to say "I don't know" —
rejected as less reliable than deterministically short-circuiting when retrieval yields
nothing above threshold, since a model-generated refusal could vary in wording or occasionally
still produce an ungrounded claim.

## 8. Reuse of Isolation Model for New Tables

**Decision**: Apply RLS to `messages` and `message_citations` following the same transitive
pattern as prior slices: `messages.project_id`/`thread_id` must resolve to a project owned by
`auth.uid()`; `message_citations` inherits isolation transitively via its parent `message_id`.

**Rationale**: Consistent with constitution Principle I and the precedent set by
001-core-foundation and 002-document-processing-pipeline; avoids introducing a new, divergent
isolation pattern for this feature.

**Alternatives considered**: None seriously considered — deviating from the established
pattern would introduce unjustified complexity and inconsistency (Principle IV).
