# Phase 0 Research: RAG Settings Panel

## 1. Settings Storage Scope & Shape

**Decision**: Store settings in a single `conversation_settings` table with a 1:1 relationship
to `conversations` (one row per thread, created with defaults when the thread is created or
lazily on first read). Fields: `web_search_enabled` (bool), `temperature` (numeric, mapped from
a plain-language creativity level), `retrieval_top_k` (int), `included_document_types`
(array/JSON of allowed type identifiers).

**Rationale**: The spec's default assumption is per-conversation scope ("apply to the current
conversation"); a 1:1 row keyed by `conversation_id` is the simplest model matching that scope
without inventing a separate settings-versioning or profile system.

**Alternatives considered**: Per-project default settings inherited by all threads — explicitly
deferred per spec Assumptions as a possible future feature, not built now to avoid
unrequested scope.

## 2. Plain-Language Creativity → Temperature Mapping

**Decision**: The frontend presents three levels (Precise / Balanced / Creative); the backend
Pydantic schema validates and stores the underlying `temperature` value, with the mapping
(e.g., 0.2 / 0.6 / 0.9) defined as a small constant table in the settings model layer, not
exposed as a raw free-form number to the user.

**Rationale**: FR-007 explicitly requires a plain-language control, not a raw numeric
parameter; keeping the mapping server-side (or in a shared constants module) prevents drift
between frontend and backend interpretations of what "Creative" means.

**Alternatives considered**: Exposing a raw slider with a visible numeric temperature value —
rejected, spec explicitly calls for non-technical, plain-language controls.

## 3. Web Search Routing as a LangGraph Node

**Decision**: Add a conditional node to the existing LangGraph flow (003-rag-project-chat)
that runs immediately after the project-scoped document retrieval step and before context
assembly/generation. The node checks the conversation's `web_search_enabled` setting; if true,
it invokes a web search tool and merges a bounded number of web results (each tagged with a
distinct "web" source type in its metadata) into the context alongside the project's document
chunks. If false, or if the web search call fails/times out, the node passes through
unmodified, falling back to document-only context.

**Rationale**: Routing as a graph node (rather than a branch buried in application code) keeps
the pipeline's stage-based structure consistent with 002/003's precedent (Principle IV) and
makes the decision point explicitly observable/testable in isolation. Failing open to
document-only context on web-search errors satisfies constitution Principle VII (graceful
failure — a web search hiccup must not fail the whole answer).

**Alternatives considered**: Making web search a hard dependency that fails the entire answer
if unavailable — rejected, violates graceful-failure principle and the spec's implicit
expectation that toggling web search off must always still work reliably.

## 4. Citation Handling for Web-Sourced Content

**Decision**: Web search results included in context are tagged with a distinct citation
type (e.g., `source_type: "web"` alongside the existing project-document citations from
003-rag-project-chat's `message_citations`), including the web result's URL/title, so the
frontend can visually distinguish web-based citations from project-document citations.

**Rationale**: FR-005 requires that web-search-sourced content still meet citation/
traceability expectations; reusing and extending the existing citation model (rather than
inventing a parallel one) keeps the codebase consistent (Principle IV) while satisfying
Principle II for the web-search case specifically.

**Alternatives considered**: Silently blending web content into the answer without a
distinguishable citation — rejected, directly conflicts with FR-005 and Principle II.

## 5. Applying Settings Without Reload / Immediate Persistence

**Decision**: The frontend settings panel holds local optimistic state for each control; on
every change, it immediately (a) updates the local UI state so the control visually reflects
the new value with no delay, and (b) fires a `PATCH` request to persist the change to
`conversation_settings`. The next `ask` request reads the persisted row fresh (no client-side
caching of settings sent with the request), so there is a single source of truth and no risk
of stale settings being (re)applied after a page reload.

**Rationale**: FR-012/FR-015 require immediate effect without reload and persistence across
reopening; optimistic local UI update + immediate persist satisfies both without requiring a
full-page or full-conversation re-render, and reading fresh server-side state on each `ask`
avoids any client/server settings drift.

**Alternatives considered**: Sending the settings payload directly with each `ask` request
instead of persisting server-side first — rejected, since FR-015 requires settings to persist
across panel close/reopen within the session, which requires server-side storage regardless.

## 6. In-Flight Generation Isolation from Setting Changes

**Decision**: The `ask` endpoint (003-rag-project-chat) reads `conversation_settings` once, at
the start of handling a given question, and captures the resolved values into that message's
processing context; a setting change that occurs after the question was submitted has no
effect on that in-flight generation, only on subsequent `ask` calls. The resolved settings
snapshot used for a given answer is persisted alongside the message (e.g., as part of the
message's citation/metadata record) for observability.

**Rationale**: Directly implements FR-013 and the corresponding edge case; snapshotting
per-request avoids any race condition where a mid-flight setting change could partially affect
an already-started retrieval or generation call.

**Alternatives considered**: Re-reading settings mid-generation (e.g., once for retrieval, again
for generation) — rejected, could produce an inconsistent answer generated under two different
configurations, which is confusing and harder to audit.

## 7. Document-Type Filter Validation

**Decision**: `included_document_types` defaults to "all known types" for the project; the
settings update endpoint validates that the array is non-empty before persisting a change,
rejecting (with a clear error) any attempt to save an empty set (FR-011).

**Rationale**: Directly implements FR-011's requirement to prevent a zero-eligible-sources
state; validating at the persistence boundary (not just the UI) ensures the constraint holds
regardless of client behavior.

**Alternatives considered**: Allowing an empty set and having retrieval silently return
nothing — rejected, spec explicitly requires preventing this silently confusing state.

## 8. Frontend Panel Composition

**Decision**: Build the panel as a `SettingsPanel` component composed of existing
`GlassPanel`/`GlassCard` primitives (001-core-foundation design system) in a collapsible
right-hand drawer, using the existing theme provider for light/dark support; no new visual
primitives are introduced.

**Rationale**: FR-016 requires visual consistency with the existing Liquid Glass system;
reusing established primitives guarantees this by construction rather than by manual review.

**Alternatives considered**: A separate settings-specific visual style — rejected, explicitly
against FR-016 and constitution Principle VI.
