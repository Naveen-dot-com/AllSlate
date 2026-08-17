# Feature Specification: Core Application Foundation

**Feature Branch**: `001-core-foundation`

**Created**: 2026-08-17

**Status**: Draft

**Input**: User description: "Build the foundation of AllSlate, an enterprise-grade document intelligence application. Product Overview: AllSlate is a multi-tenant RAG-based PWA where users can create projects, maintain isolated project-specific knowledge and conversations, and eventually upload and query documents using AI. This specification covers the core application foundation: authentication, project management, project isolation, conversation management, navigation, and the overall product experience. Includes: (1) Authentication via Google Auth through Supabase Auth, with first-time user experience guiding new users to create their first project; (2) Project Management — create, name, describe, list, open/switch, and return to projects, with server-side ownership enforcement; (3) Project Isolation as a core security requirement covering conversations, threads, messages, documents, document metadata, processing state, embeddings, retrieved context, and project-specific knowledge, enforced via both API-level ownership checks and database-level Row Level Security; (4) Project Chat — each project has its own dedicated chat experience reachable via User → Project → Project-specific Chat."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Sign In and Reach My Workspace (Priority: P1)

A new or returning user opens AllSlate and signs in with their Google account so they can
securely access their own private workspace, without needing to remember a separate password.

**Why this priority**: Without authentication, no other part of the product can be used or
secured. This is the entry point and the foundation for all tenant isolation guarantees.

**Independent Test**: Can be fully tested by opening the app while signed out, confirming no
application content is accessible, completing Google sign-in, and confirming a session is
established and persists across a page refresh.

**Acceptance Scenarios**:

1. **Given** a user is not signed in, **When** they open AllSlate, **Then** they are presented
   with a sign-in screen and cannot view any project, conversation, or document data.
2. **Given** a user completes Google sign-in successfully for the first time, **When** the
   sign-in flow completes, **Then** an application profile is created for them and they are
   authenticated.
3. **Given** an already-registered user completes Google sign-in, **When** the sign-in flow
   completes, **Then** their existing application profile is retrieved (not duplicated) and
   they are authenticated.
4. **Given** an authenticated user, **When** they refresh the browser or reopen the app, **Then**
   they remain signed in without re-authenticating.
5. **Given** an authenticated user, **When** they choose to sign out, **Then** their session is
   terminated and they are returned to the sign-in screen with no further access to
   application data.

---

### User Story 2 - First-Time User Is Guided to Create a Project (Priority: P1)

A user who has just signed in for the first time, and has no existing projects, is guided
immediately into creating their first project so they can start using AllSlate right away
without confusion about what to do next.

**Why this priority**: Projects are the primary organizational unit of the product; a user
with zero projects has no meaningful way to use the application, so this onboarding step is
essential to first-run value.

**Independent Test**: Can be fully tested by signing in as a brand-new user with zero projects
and confirming the user is directed into a project-creation flow rather than an empty or
ambiguous screen.

**Acceptance Scenarios**:

1. **Given** a newly authenticated user with no projects, **When** sign-in completes, **Then**
   the user is guided directly into creating their first project.
2. **Given** a user who already has at least one project, **When** they sign in, **Then** they
   are taken to their project list/workspace rather than forced into project creation.

---

### User Story 3 - Create, View, and Switch Between Projects (Priority: P1)

A signed-in user creates one or more projects, each with a name and description, views all of
their projects in a list, and switches between them to work in different isolated contexts.

**Why this priority**: Project management is the core organizing capability of AllSlate;
without it, users cannot separate their work into isolated contexts, which is the product's
central value proposition.

**Independent Test**: Can be fully tested by creating multiple projects with distinct names
and descriptions, confirming they all appear in the project list, and confirming that
switching between them changes the active project context.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** they create a project with a name and description,
   **Then** the project is saved and appears in their project list.
2. **Given** a user with multiple projects, **When** they view their project list, **Then**
   each entry shows the project name, description (or summary), and which project (if any) is
   currently active.
3. **Given** a user viewing their project list, **When** they select a different project,
   **Then** that project becomes the active project and its context (chat, documents) loads.
4. **Given** a user viewing their project list, **When** they look for a way to start something
   new, **Then** there is an obvious, clearly visible action to create a new project.
5. **Given** a user has created a project previously, **When** they return to the application
   later, **Then** that project is still listed and can be reopened.

---

### User Story 4 - Projects Are Fully Isolated From Each Other and Other Users (Priority: P1)

As a user works within a project, all of that project's conversations, documents, and derived
knowledge remain completely separate from every other project — whether owned by the same user
or a different user — so that information never leaks across boundaries.

**Why this priority**: Isolation is a stated non-negotiable security requirement of the product
(per the project constitution). Any leakage across users or projects is a critical failure,
independent of how polished other features are.

**Independent Test**: Can be fully tested by creating two projects (as the same user, and
separately as two different users), adding distinct conversations/data to each, and confirming
that no API request or UI view for one project ever returns or displays data belonging to the
other project or the other user.

**Acceptance Scenarios**:

1. **Given** two projects owned by the same user, **When** the user opens Project A, **Then**
   no conversations, messages, or document data from Project B are visible or retrievable.
2. **Given** two different users each with their own project, **When** either user makes a
   request for project or conversation data, **Then** the request only ever succeeds for
   projects they own, and requests for the other user's project are rejected.
3. **Given** any API request that references a project, **When** the request is processed,
   **Then** the system validates both that the requester is authenticated and that the
   requester owns (or is otherwise authorized for) the referenced project before returning
   any data.
4. **Given** a user attempts to access a project ID that does not belong to them (e.g., by
   guessing or modifying a request), **When** the request is made, **Then** access is denied
   and no project data is disclosed.

---

### User Story 5 - Dedicated Chat Per Project (Priority: P2)

When a user opens a project, they land in that project's own dedicated chat experience, scoped
entirely to that project's context.

**Why this priority**: This establishes the navigation and UX flow (User → Project → Chat) and
the conversation scoping model that later document-upload and retrieval features will build on.
It depends on projects and isolation (P1 stories) already existing.

**Independent Test**: Can be fully tested by opening a project and confirming a chat interface
is presented that is uniquely associated with that project, and that switching to a different
project shows a different (or empty) chat history rather than the same one.

**Acceptance Scenarios**:

1. **Given** an authenticated user opens a project, **When** the project loads, **Then** the
   project's dedicated chat view is displayed.
2. **Given** a user has separate conversations in Project A and Project B, **When** they switch
   from Project A to Project B, **Then** the chat view updates to show only Project B's
   conversation history.
3. **Given** a user opens a brand-new project with no prior activity, **When** the project's
   chat view loads, **Then** it shows an empty conversation state rather than any other
   project's history.

---

### Edge Cases

- What happens when a user's Google sign-in succeeds but application profile creation fails
  partway through (e.g., transient database error)? The user must not be left in a state where
  they appear authenticated but have no usable profile; the system must surface a clear error
  and allow retry without creating duplicate or corrupted profile records.
- How does the system handle a user attempting to create a project with an empty name, or a
  name/description exceeding reasonable length limits?
- What happens when a user has many (e.g., dozens or hundreds of) projects — does the project
  list remain usable (e.g., via scrolling, search, or pagination)?
- How does the system handle a user's session expiring while they are actively viewing a
  project or chat — do they get a clear re-authentication prompt without losing unsent input
  or being shown stale/incorrect project data?
- What happens if two browser tabs are open with different active projects for the same user —
  does each tab correctly maintain its own active-project context?
- How does the system respond when a request references a project ID that does not exist at
  all (deleted or never created), versus one that exists but belongs to another user? Both
  must be denied without revealing which case occurred (to avoid leaking existence
  information about other users' projects).
- What happens when a user tries to sign in with a Google account but declines to grant the
  requested permissions?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST require users to authenticate via Google sign-in before granting
  access to any application content (projects, conversations, documents).
- **FR-002**: The system MUST create an application profile for a user upon their first
  successful sign-in, and MUST retrieve (not duplicate) their existing profile on subsequent
  sign-ins.
- **FR-003**: The system MUST maintain an authenticated session that persists across browser
  refreshes until the user explicitly signs out or the session naturally expires.
- **FR-004**: The system MUST provide a sign-out action that terminates the user's session and
  prevents further access to application data until they re-authenticate.
- **FR-005**: The system MUST never expose authentication secrets or backend service
  credentials to the client/frontend.
- **FR-006**: The system MUST determine, immediately after a user's first sign-in, whether
  they have any existing projects, and MUST guide users with zero projects directly into a
  project-creation flow.
- **FR-007**: The system MUST allow an authenticated user to create a project by supplying a
  name and a description.
- **FR-008**: The system MUST allow an authenticated user to view a list of all projects they
  own.
- **FR-009**: The project list MUST display, for each project, its name, its description (or a
  useful summary), and a clear indication of whether it is the currently active project.
- **FR-010**: The system MUST allow an authenticated user to switch their active project from
  the project list.
- **FR-011**: The project list MUST provide an obvious, discoverable action for creating a new
  project.
- **FR-012**: The system MUST allow a user to create any number of projects and to return to
  and reopen any previously created project.
- **FR-013**: Every project MUST belong to exactly one owning user, and MUST have a unique
  identifier.
- **FR-014**: The system MUST enforce project ownership server-side for every operation that
  creates, reads, updates, or deletes a project or its associated data — never relying on
  frontend checks alone.
- **FR-015**: The system MUST reject any request (API or otherwise) where the authenticated
  user does not own the referenced project, without disclosing whether the project exists
  under another owner.
- **FR-016**: The system MUST scope all project-level data access using the authenticated
  user's identity combined with the target project's identity on every request.
- **FR-017**: The system MUST treat conversations, conversation threads, messages, documents,
  document metadata, document processing state, embeddings, retrieved context, and
  project-specific knowledge as data that belongs entirely to a single project's isolation
  boundary.
- **FR-018**: The system MUST NOT allow any project to access, retrieve, or display another
  project's conversations, documents, embeddings, or derived knowledge, regardless of whether
  the two projects share the same owning user.
- **FR-019**: Any AI retrieval operation MUST be scoped exclusively to the currently active
  project's data.
- **FR-020**: The system MUST use database-level access control policies (e.g., row-level
  security) to enforce user- and project-level data isolation, in addition to
  application-level checks, so that isolation does not depend solely on frontend or API-layer
  logic.
- **FR-021**: When a user opens a project, the system MUST present that project's own dedicated
  chat experience, scoped to that project only.
- **FR-022**: The system MUST ensure that navigating between projects updates the chat view to
  reflect only the newly active project's conversation history.

### Key Entities

- **User Profile**: Represents an authenticated individual using AllSlate. Linked one-to-one
  with a Google-authenticated identity. Owns zero or more projects.
- **Project**: The primary organizational and isolation boundary in AllSlate. Has a unique
  identifier, a name, a description, an owning user, and a creation time. All conversations,
  documents, and derived knowledge belong to exactly one project.
- **Conversation**: A project-scoped chat context containing an ordered sequence of messages.
  Belongs to exactly one project and is not visible outside that project.
- **Message**: A single turn within a conversation (from the user or the system/AI). Belongs to
  exactly one conversation, which belongs to exactly one project.
- **Session**: Represents an authenticated user's active login state, established at sign-in
  and terminated at sign-out or expiration.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of unauthenticated access attempts to project, conversation, or document
  data are blocked, with zero exceptions observed in testing.
- **SC-002**: A new user can go from opening the sign-in screen to landing in their first
  created project's chat in under 60 seconds.
- **SC-003**: In cross-project and cross-user isolation testing, 0 instances of one project's
  or user's data (conversations, documents, embeddings) are ever returned to another
  project or user.
- **SC-004**: Users can switch their active project and see the correct project's chat history
  load in under 2 seconds under normal conditions.
- **SC-005**: A returning user's session persists across a browser refresh in 100% of test
  cases, without requiring re-authentication.
- **SC-006**: 95% of first-time users successfully create their first project without
  additional guidance or support beyond the guided onboarding flow.
- **SC-007**: A user can locate and use the "create new project" action from the project list
  without hesitation in usability testing (no more than one incorrect click before finding it).

## Assumptions

- Google is the only identity provider required for this foundation; other providers (e.g.,
  Microsoft, email/password) are out of scope for this feature.
- Supabase Auth is used as the authentication/session provider, with Google as the configured
  OAuth provider; underlying session token mechanics follow Supabase's standard session model.
- Document upload, processing, and retrieval pipelines themselves (partitioning, chunking,
  embedding, vectorization) are out of scope for this specification — this feature only
  establishes the project boundary and dedicated chat entry point that those capabilities will
  later plug into.
- Project descriptions are plain text with a reasonable maximum length (exact limit to be
  defined at implementation time); no rich-text or attachment support is assumed for
  descriptions.
- There is no project sharing or multi-user collaboration within a single project in this
  foundation; every project has exactly one owner and is not shared with other users.
- Deleting or archiving projects is not explicitly required by this specification; only
  create, list, view, and switch are in scope. Deletion may be addressed in a future feature.
- Rate limiting, CAPTCHA, or other abuse-prevention measures for sign-in are assumed to follow
  Supabase/Google's standard defaults unless a future spec states otherwise.
