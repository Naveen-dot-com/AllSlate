# Feature Specification: RAG Settings Panel

**Feature Branch**: `004-rag-settings-panel`

**Created**: 2026-08-17

**Status**: Draft

**Input**: User description: "Give the user a settings panel, positioned on the right side of the chat screen and associated with the project's Knowledge Base, where they can control how questions are answered. From this panel, the user can turn supplementary web search on or off, adjust the response's creativity/temperature, and adjust other retrieval-related options relevant to RAG — for example, how many source chunks are retrieved, or which document types within the project are included. These settings should be easy to find and understand for a non-technical user, visually consistent with the rest of the Liquid Glass design system, and should apply to the current conversation without requiring a page reload."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Discover and Open Retrieval Settings (Priority: P1)

A user in a project's chat notices a settings panel associated with the project's Knowledge
Base, positioned on the right side of the chat screen, and opens it to see the controls
available for how their questions get answered.

**Why this priority**: If users cannot easily find or understand that these controls exist,
none of the underlying capabilities (web search toggle, creativity, retrieval tuning) deliver
any value. Discoverability is the entry point for every other story in this feature.

**Independent Test**: Can be fully tested by opening a project's chat screen and confirming a
clearly labeled settings panel is visible/accessible on the right side, without needing prior
knowledge of where it is.

**Acceptance Scenarios**:

1. **Given** a user has an open project's chat screen, **When** the screen loads, **Then** a
   settings panel associated with the project's Knowledge Base is visible or easily accessible
   on the right side of the chat screen.
2. **Given** a user opens the settings panel for the first time, **When** they view it,
   **Then** each control has a clear, plain-language label and description understandable
   without technical background (e.g., no unexplained jargon like "top-k" or "temperature"
   without a plain-language cue).
3. **Given** a user is unfamiliar with RAG or AI terminology, **When** they view the panel,
   **Then** they can understand what each setting does well enough to make an informed choice.

---

### User Story 2 - Toggle Supplementary Web Search (Priority: P1)

A user turns supplementary web search on or off for their project's chat, controlling whether
answers may draw on information beyond the project's uploaded documents.

**Why this priority**: This is an explicit, named capability in the request and directly
affects source-fidelity expectations (whether an answer might include external, unverified
information) — a core trust concern for the product, so it ranks alongside discoverability.

**Independent Test**: Can be fully tested by toggling the web search setting on, asking a
question, confirming the behavior reflects that setting (e.g., answer sourcing behavior or
disclosure changes accordingly), then toggling it off and confirming the difference.

**Acceptance Scenarios**:

1. **Given** a user opens the settings panel, **When** they view it, **Then** there is a clear
   on/off control for supplementary web search.
2. **Given** supplementary web search is turned on, **When** the user asks a question,
   **Then** the system may include external, non-project source material in forming the
   answer (subject to normal citation/traceability expectations).
3. **Given** supplementary web search is turned off, **When** the user asks a question,
   **Then** the system only uses the project's own documents as source material, never
   external web content.
4. **Given** a user changes the web search setting, **When** they ask their next question in
   the same conversation, **Then** the new setting takes effect immediately without a page
   reload.

---

### User Story 3 - Adjust Response Creativity (Priority: P2)

A user adjusts a creativity control that influences how conservative or exploratory generated
answers are, using a plain-language control rather than a raw technical parameter.

**Why this priority**: This gives users meaningful influence over answer style, but it is a
refinement on top of the core answer-grounding behavior (Stories 1–2, 4) rather than a
blocking capability.

**Independent Test**: Can be fully tested by adjusting the creativity control to a lower and
then a higher setting, asking the same question at each setting, and confirming the control
is applied to subsequent answers without a page reload.

**Acceptance Scenarios**:

1. **Given** a user opens the settings panel, **When** they view it, **Then** there is a
   clearly labeled creativity control (e.g., a slider or a small set of plain-language levels
   such as "Precise," "Balanced," "Creative") rather than an unexplained raw numeric parameter.
2. **Given** a user adjusts the creativity control, **When** they ask their next question in
   the same conversation, **Then** the new creativity setting is applied to that answer.
3. **Given** a user has not changed the creativity control, **When** they ask a question,
   **Then** a sensible default level is used.

---

### User Story 4 - Tune Retrieval Behavior (Priority: P2)

A user adjusts retrieval-related options — such as how many source chunks are retrieved per
question and which document types within the project are eligible to be searched — to
control how broad or narrow the system's search of the Knowledge Base is.

**Why this priority**: This provides valuable control for power users refining answer
relevance/scope, but the chat is fully usable with sensible defaults without it, making it a
secondary priority behind the core toggles.

**Independent Test**: Can be fully tested by changing the retrieval breadth (e.g., number of
source chunks) and the included document-type filter, then asking a question and confirming
the retrieval behavior and/or the citations shown reflect the updated settings.

**Acceptance Scenarios**:

1. **Given** a user opens the settings panel, **When** they view it, **Then** there is a
   clearly labeled control for how many source chunks are considered when answering a
   question.
2. **Given** a user opens the settings panel, **When** they view it, **Then** there is a
   clearly labeled control for including or excluding specific document types present in the
   project's Knowledge Base.
3. **Given** a user narrows the included document types, **When** they ask a question,
   **Then** the answer's supporting citations are drawn only from the included document
   types.
4. **Given** a user changes a retrieval setting, **When** they ask their next question in the
   same conversation, **Then** the updated setting is applied immediately without a page
   reload.

---

### User Story 5 - Settings Apply to the Current Conversation Without Reloading (Priority: P1)

Whenever a user changes any setting in the panel, the change takes effect for their ongoing
conversation immediately, without requiring the page to reload or the conversation to be lost.

**Why this priority**: This is an explicit requirement in the request and underlies the
usability of every other story — if changes required a reload, the panel would feel broken
and disconnected from the live chat experience, regardless of which specific setting is
involved.

**Independent Test**: Can be fully tested by changing any setting mid-conversation and
confirming both that no reload occurs and that the existing conversation history remains
intact and unaffected.

**Acceptance Scenarios**:

1. **Given** a user is in an active conversation with existing message history, **When** they
   change any setting in the panel, **Then** the page does not reload and the existing message
   history remains visible and unaffected.
2. **Given** a user changes a setting, **When** they immediately ask a new question, **Then**
   the new setting is already in effect for that question's answer.

---

### Edge Cases

- What happens when a user changes settings while a previous answer is still being generated?
  The in-progress answer should complete using the settings that were in effect when it was
  submitted, and the new settings should apply only to subsequent questions.
- What happens if a user turns off supplementary web search after previously receiving an
  answer that used web content? Previously delivered answers and their citations remain
  unchanged; only future questions are affected.
- What happens if a user selects zero document types to include? The system must prevent this
  or clearly explain that at least one document type (or "all documents") must remain
  selected, rather than silently retrieving nothing.
- What happens if the project's Knowledge Base contains no documents of a given type? That
  document-type option should still be understandable (e.g., shown as available but with no
  current matches) rather than confusing or broken.
- What happens when a new user opens the panel for the first time with no prior customization?
  All settings must show sensible, clearly indicated default values.
- Do settings apply per-conversation-thread, or per-project across all threads? The system
  must behave consistently and communicate this scope clearly to the user (see Assumptions for
  the default scope chosen).
- What happens if a user closes the settings panel and returns to it later in the same
  session? Previously chosen settings for that scope must still be reflected, not reset to
  defaults.
- What happens when supplementary web search is turned on but a particular question doesn't
  need it? The system should not force external content into an answer that is already fully
  supported by the project's own documents.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a settings panel associated with the project's
  Knowledge Base, positioned on the right side of the chat screen.
- **FR-002**: The settings panel MUST be easy to find and open from the chat screen without
  requiring the user to navigate away from their conversation.
- **FR-003**: Every control in the settings panel MUST be labeled and described in
  plain, non-technical language understandable to a user unfamiliar with AI/RAG terminology.
- **FR-004**: The system MUST provide a control to turn supplementary web search on or off.
- **FR-005**: When supplementary web search is on, the system MAY include external,
  non-project source material when forming an answer, subject to the same citation and
  traceability expectations as project-document sources.
- **FR-006**: When supplementary web search is off, the system MUST restrict answer sourcing
  to the project's own documents only, never external web content.
- **FR-007**: The system MUST provide a plain-language control for adjusting response
  creativity (e.g., named levels rather than an unexplained raw numeric value), which
  influences how conservative or exploratory generated answers are.
- **FR-008**: The system MUST apply a sensible default creativity level when the user has not
  explicitly changed it.
- **FR-009**: The system MUST provide a control for adjusting how many source chunks are
  retrieved and considered when answering a question.
- **FR-010**: The system MUST provide a control for including or excluding specific document
  types present within the project's Knowledge Base from retrieval.
- **FR-011**: The system MUST prevent a user from excluding all document types (leaving zero
  eligible sources) without a clear alternative (e.g., requiring at least one type, or an
  explicit "search nothing" state the user must knowingly confirm is not offered).
- **FR-012**: The system MUST apply any changed setting to the user's next question within the
  active conversation without requiring a page reload.
- **FR-013**: The system MUST NOT alter the settings that were in effect for an answer that is
  already being generated when a setting changes; only subsequent questions use the new
  settings.
- **FR-014**: The system MUST NOT alter previously delivered answers or their citations when
  settings are changed afterward.
- **FR-015**: The system MUST persist a user's chosen settings for a conversation for the
  duration of their session so that reopening the panel reflects their prior choices rather
  than resetting to defaults.
- **FR-016**: The settings panel's visual design MUST be consistent with the rest of the
  application's Liquid Glass design system, including support for both light and dark mode.
- **FR-017**: The system MUST enforce that all retrieval and settings operations remain scoped
  to the active project and its owning user, consistent with the isolation model established
  in 001-core-foundation.

### Key Entities

- **Retrieval Settings**: The set of user-adjustable controls affecting how a conversation's
  questions are answered: supplementary web search (on/off), response creativity level,
  number of source chunks retrieved, and included/excluded document types. Associated with a
  conversation (and, transitively, its project).
- **Document Type**: A category of uploaded document content (as established by
  002-document-processing-pipeline) that can be individually included or excluded from
  retrieval via the settings panel.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 95% of users in usability testing can locate and open the settings panel
  without assistance.
- **SC-002**: 90% of non-technical users in usability testing can correctly describe, in their
  own words, what at least three of the panel's controls do after viewing it.
- **SC-003**: 100% of setting changes take effect for the next question asked in the same
  conversation, with 0 page reloads observed.
- **SC-004**: 100% of answers generated while supplementary web search is off contain zero
  external, non-project source citations, across testing.
- **SC-005**: 100% of previously delivered answers remain unchanged after a subsequent setting
  change, across testing.
- **SC-006**: A user can change any setting and receive a new answer reflecting that change in
  under the same response time as a normal question (no added latency attributable to the
  settings panel itself).

## Assumptions

- This feature builds on 001-core-foundation (projects, auth, isolation), 
  002-document-processing-pipeline (document types, chunk metadata), and
  003-rag-project-chat (conversation threads, retrieval, generation, streaming); it does not
  redefine those foundations, only adds user-configurable controls over their existing
  behavior.
- Settings apply per-conversation-thread (not globally across all of a project's threads) by
  default, since the request describes them as applying "to the current conversation"; a
  future feature may add project-wide default settings if needed.
- Settings persist for the duration of the user's session/thread (i.e., remain in effect when
  returning to that thread) but are not required to sync across devices or be explicitly
  exported/imported in this specification.
- "Creativity" is presented to users as a small number of plain-language levels (e.g.,
  Precise/Balanced/Creative) mapped internally to a generation parameter; the exact numeric
  mapping is an implementation detail not prescribed here.
- Supplementary web search, when enabled, is still subject to the product's general
  traceability and citation expectations — external sources used in an answer must still be
  identifiable to the user, consistent with the constitution's Retrieval Accuracy & Source
  Fidelity principle.
- Document type categories offered in the filter correspond to the typed element/document
  categories already established by 002-document-processing-pipeline (e.g., distinguishing by
  file type or content type), not a new taxonomy invented by this feature.
- There is no requirement in this specification for administrators or other users to see or
  override another user's settings choices, consistent with the single-owner-per-project model.
