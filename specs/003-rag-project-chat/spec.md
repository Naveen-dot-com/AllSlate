# Feature Specification: RAG Project Chat

**Feature Branch**: `003-rag-project-chat`

**Created**: 2026-08-17

**Status**: Draft

**Input**: User description: "Within a project's chat, a user asks natural-language questions and receives answers grounded in that project's uploaded documents. Answers should be accurate and traceable back to the source material — the user should be able to tell what the answer is based on. When an answer draws on a table or image from a document, the response includes that original table or image, not just a text description of it. The chat supports multiple separate conversation threads per project, as described earlier, and each thread keeps its own message history. The chat experience should feel fast and responsive even while an answer is being generated, and should clearly communicate when it's retrieving information versus generating a response."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ask a Question and Get a Grounded, Traceable Answer (Priority: P1)

A user opens a project's chat, asks a natural-language question, and receives an answer that
is based on the project's uploaded documents, with a clear indication of which source
document(s) and location(s) the answer draws from.

**Why this priority**: This is the core value proposition of AllSlate — grounded,
trustworthy answers from a user's own documents. Without it, the chat is not meaningfully
different from a generic chatbot and the product delivers no unique value.

**Independent Test**: Can be fully tested by asking a question whose answer clearly exists in
a previously processed document and confirming the response text is accurate and accompanied
by a visible reference to the specific source document (and location within it) it was drawn
from.

**Acceptance Scenarios**:

1. **Given** a project with at least one fully processed document containing the relevant
   information, **When** the user asks a question about that information, **Then** the system
   returns an answer along with a visible reference to the source document(s) and location(s)
   (e.g., page or section) the answer is based on.
2. **Given** a project whose documents do not contain information relevant to the user's
   question, **When** the user asks that question, **Then** the system clearly indicates that
   it could not find sufficient supporting information, rather than fabricating an answer.
3. **Given** an answer that is grounded in multiple source locations, **When** the user views
   the response, **Then** all contributing sources are indicated, not just one.
4. **Given** a user wants to verify an answer, **When** they inspect the cited source
   reference, **Then** they can identify the exact document and location the system used,
   consistent with the source-traceability metadata established by the document processing
   pipeline.

---

### User Story 2 - See the Original Table or Image, Not Just a Description (Priority: P1)

When an answer is grounded in a table or image from a document, the user sees that original
table or image displayed as part of the response, rather than only a text description of it.

**Why this priority**: Tables and images often carry precise information (numbers, layouts,
visual detail) that a text summary cannot fully capture; presenting the original asset is
essential for the user to trust and correctly interpret the answer. This is a direct
extension of the traceability guarantee established by the document processing pipeline.

**Independent Test**: Can be fully tested by asking a question whose best-supporting evidence
is a table or image within a processed document, and confirming the chat response displays
the original table/image asset (not only its AI-generated summary) alongside the answer text.

**Acceptance Scenarios**:

1. **Given** an answer that is grounded primarily in a table from a document, **When** the
   response is shown, **Then** the original table is displayed within the response, not only a
   textual description of its contents.
2. **Given** an answer that is grounded primarily in an image from a document, **When** the
   response is shown, **Then** the original image is displayed within the response.
3. **Given** an answer grounded in a mix of text and a table/image, **When** the response is
   shown, **Then** both the textual answer and the relevant original table/image are presented
   together, with a clear association between them.

---

### User Story 3 - Maintain Multiple Independent Conversation Threads Per Project (Priority: P2)

A user creates and switches between multiple separate conversation threads within the same
project, with each thread keeping its own independent message history.

**Why this priority**: This extends the project chat foundation (from 001-core-foundation)
to support organizing distinct lines of inquiry within a project. It is important for
usability at scale but the single-thread question-answering experience (User Story 1) must
work first.

**Independent Test**: Can be fully tested by creating two conversation threads within the
same project, asking different questions in each, and confirming that switching between
threads shows only that thread's own message history with no cross-contamination.

**Acceptance Scenarios**:

1. **Given** a user is in a project, **When** they start a new conversation thread, **Then** a
   new, empty thread is created without affecting any existing thread's history.
2. **Given** a project with multiple threads, **When** the user switches from one thread to
   another, **Then** only the selected thread's message history is displayed.
3. **Given** a user asks questions in Thread A, **When** they later view Thread B in the same
   project, **Then** Thread B does not contain any of Thread A's questions or answers.
4. **Given** a user returns to a previously used thread, **When** they reopen it, **Then** its
   full prior message history is still present.

---

### User Story 4 - Responsive Chat With Clear Retrieval vs. Generation Feedback (Priority: P2)

While an answer is being produced, the user sees the chat remain responsive, with clear,
distinct feedback indicating whether the system is currently retrieving supporting
information or generating the response text.

**Why this priority**: This is a trust and perceived-performance requirement layered on top
of the core question-answering flow; the product is usable without this polish but noticeably
less trustworthy and pleasant without it, especially for slower queries.

**Independent Test**: Can be fully tested by asking a question and observing that the UI
displays a distinct "retrieving" state before switching to a distinct "generating" state, and
that the rest of the application (navigation, other UI controls) remains usable throughout.

**Acceptance Scenarios**:

1. **Given** a user submits a question, **When** the system begins searching the project's
   documents for supporting information, **Then** the UI clearly indicates a "retrieving"
   state distinct from a "generating" state.
2. **Given** retrieval has completed and answer generation has begun, **When** the user views
   the chat, **Then** the UI updates to clearly indicate a "generating" state.
3. **Given** an answer is actively being generated, **When** the user interacts with other
   parts of the application (e.g., switching projects or threads), **Then** those interactions
   are not blocked or delayed by the in-progress generation.
4. **Given** a question takes noticeably longer than usual to answer, **When** the user
   continues waiting, **Then** the UI continues to indicate active progress rather than
   appearing frozen or unresponsive.

---

### Edge Cases

- What happens when a user asks a question in a project that has no processed (stored)
  documents at all? The system must clearly state there is no available source material,
  rather than attempting to answer from general knowledge.
- What happens when a user asks a question while some of the project's documents are still
  processing (not yet "stored")? The system should clearly indicate that some documents are
  not yet available for retrieval, and should not present an answer as fully grounded if it
  omits still-processing content.
- How does the system handle a question that is ambiguous or too broad to answer from the
  available documents? The system should indicate uncertainty or ask for clarification rather
  than guessing.
- What happens if the retrieval step finds candidate source material but the generation step
  fails or times out? The user must see a clear error state for that specific message, and the
  failed attempt must not corrupt the thread's message history or leave it in an ambiguous
  state.
- What happens if a cited source document or asset (table/image) is later deleted or becomes
  inaccessible? Previously delivered answers' citations should degrade gracefully (e.g.,
  indicate the source is no longer available) rather than breaking the chat view.
- What happens when a user sends a new message before the previous answer has finished
  generating? The system must handle concurrent or rapid-fire messages within a thread
  without losing, duplicating, or misordering messages.
- How does the system prevent an answer for one project from ever being grounded in another
  project's documents, even accidentally? Retrieval must be strictly scoped to the active
  project's stored documents only.
- What happens when a user switches active project or thread while an answer is still being
  generated for a previous message? The in-progress generation must complete safely in the
  background and be correctly associated with its original thread rather than the newly
  active one.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST allow an authenticated user to ask a natural-language question
  within an open project's chat.
- **FR-002**: The system MUST generate answers that are grounded in the content of the active
  project's stored (fully processed) documents, and MUST NOT present fabricated or
  unsupported claims as fact.
- **FR-003**: Every answer MUST include a visible reference to the specific source
  document(s) and location(s) (e.g., page or section) it was derived from.
- **FR-004**: When an answer draws on multiple source locations, the system MUST indicate all
  contributing sources, not only a single one.
- **FR-005**: When sufficient supporting evidence cannot be found in the active project's
  documents, the system MUST clearly communicate that no adequate answer could be produced,
  rather than guessing.
- **FR-006**: When an answer is grounded in a table element, the response MUST display the
  original table (not only a generated text description of it).
- **FR-007**: When an answer is grounded in an image element, the response MUST display the
  original image (not only a generated text description of it).
- **FR-008**: When an answer draws on both textual content and a table/image, the response
  MUST present the text and the original table/image together with a clear association
  between them.
- **FR-009**: The system MUST allow a user to create a new, independent conversation thread
  within a project at any time.
- **FR-010**: Each conversation thread MUST maintain its own message history, independent of
  any other thread in the same project.
- **FR-011**: The system MUST allow a user to switch between conversation threads within a
  project, displaying only the selected thread's message history.
- **FR-012**: The system MUST persist each thread's message history so it remains available
  when the user returns to that thread later.
- **FR-013**: The system MUST scope retrieval and answer generation strictly to the currently
  active project's stored documents, and MUST NOT allow another project's documents to
  contribute to an answer.
- **FR-014**: The system MUST indicate to the user, in real time, when it is retrieving
  supporting information for a question, distinct from when it is generating the response
  text.
- **FR-015**: The system MUST remain responsive to other user interactions (e.g., navigation,
  switching projects/threads) while an answer is being retrieved or generated.
- **FR-016**: If answer generation fails or times out after retrieval has completed, the
  system MUST surface a clear error state for that specific message without corrupting the
  thread's existing message history.
- **FR-017**: The system MUST indicate to the user when some of the active project's documents
  are not yet fully processed and therefore not yet available as retrieval sources.
- **FR-018**: The system MUST handle a new message submitted while a previous answer in the
  same thread is still generating without losing, duplicating, or misordering messages.
- **FR-019**: If a user navigates away from a thread while its answer is still generating, the
  system MUST complete that generation safely in the background and associate the result with
  its originating thread.
- **FR-020**: The system MUST enforce project and thread ownership server-side for every
  operation that reads or writes conversation messages, consistent with the isolation model
  established in 001-core-foundation.

### Key Entities

- **Conversation Thread**: An independent, project-scoped chat context with its own message
  history. Belongs to exactly one project (extends the `Conversation` entity from
  001-core-foundation).
- **Message**: A single turn within a conversation thread (user question or system answer).
  For system answers, includes generated response text, an in-progress state (retrieving /
  generating / complete / failed), and zero or more source citations.
- **Source Citation**: A reference attached to an answer message identifying the exact source
  document, location (e.g., page/section), and — when applicable — the original table/image
  asset that contributed to the answer. Builds directly on the chunk-level traceability
  metadata established by the document processing pipeline.
- **Retrieval Result**: The set of source chunks (and their associated documents/assets)
  identified as relevant to a given question, used to ground the generated answer and to
  populate its source citations.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of delivered answers include at least one visible, verifiable source
  citation, or an explicit "insufficient information" indication — never an uncited,
  unqualified answer.
- **SC-002**: In evaluation testing against known question/answer pairs derived from uploaded
  documents, at least 90% of answers are judged accurate and adequately grounded by their
  cited sources.
- **SC-003**: 100% of answers grounded in a table or image display the original table/image
  asset, not only a text description, in testing.
- **SC-004**: Users see a distinct "retrieving" indicator within 1 second of submitting a
  question, and a distinct "generating" indicator once retrieval completes, in 95% of observed
  cases.
- **SC-005**: 0 instances of one project's documents contributing to another project's answer,
  across isolation testing.
- **SC-006**: Users can switch between conversation threads and see the correct, independent
  message history load in under 2 seconds.
- **SC-007**: The rest of the application (navigation, project/thread switching) remains fully
  usable during 100% of tested in-progress answer generations, with no observed blocking.
- **SC-008**: 0 instances of message loss, duplication, or misordering when a user sends a new
  message while a previous answer in the same thread is still generating, across concurrency
  testing.

## Assumptions

- This feature builds directly on 001-core-foundation (auth, projects, isolation, per-project
  chat navigation) and 002-document-processing-pipeline (stored documents, chunks with
  source-traceability metadata, table/image asset references); it does not redefine those
  foundations.
- Only documents that have reached "stored" status (per 002-document-processing-pipeline) are
  eligible as retrieval sources; documents still processing are excluded from grounding but
  the user is informed they exist and are pending.
- "Real time" retrieving/generating indicators mean the user perceives no polling delay (on
  the order of a second or less to first indicator); the exact streaming/delivery mechanism is
  an implementation detail and not prescribed by this specification.
- A conversation thread's message history has no explicit maximum length defined by this
  specification; any practical limits are an implementation detail.
- Source citations reference document/page/section-level location as established by the
  document processing pipeline's chunk metadata; deeper citation granularity (e.g., exact
  sentence highlighting) is not required for this slice.
- Editing or deleting previously sent messages is out of scope for this specification; only
  sending new messages and viewing history are covered.
- Multi-user collaboration within a single conversation thread (two people chatting in the
  same thread simultaneously) is out of scope; each project remains single-owner per
  001-core-foundation.
