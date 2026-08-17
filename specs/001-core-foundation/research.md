# Phase 0 Research: Core Application Foundation

## 1. Authentication Provider Integration

**Decision**: Use Supabase Auth with Google as the sole OAuth provider. Frontend uses
`@supabase/ssr` to manage session cookies across Next.js server/client boundaries; backend
validates the Supabase-issued JWT on every request (signature + expiry check against
Supabase's JWKS/secret) rather than re-implementing session storage.

**Rationale**: Supabase Auth already issues standards-based JWTs containing the user's
Supabase `sub` (user id), which can be verified independently by FastAPI without a shared
session store, keeping the backend stateless and horizontally scalable. `@supabase/ssr` is
the supported pattern for Next.js App Router to keep auth cookies valid across server
components, route handlers, and client components.

**Alternatives considered**:
- Custom email/password auth — rejected, user explicitly requires Google OAuth via Supabase.
- Backend-issued session cookies separate from Supabase — rejected as redundant; would
  duplicate session lifecycle management Supabase already provides.

## 2. Session Expiry Policy

**Decision**: Use Supabase's default access-token/refresh-token model: short-lived access
token (~1 hour) silently refreshed via a longer-lived refresh token (Supabase default ~ a
number of days, configurable in the Supabase project), so a user's browser session persists
across refreshes for an extended period without manual re-login, while individual JWTs stay
short-lived for security.

**Rationale**: This matches constitution Principle I (secure defaults) while satisfying
spec requirement FR-003 (session persists across refresh) without introducing custom token
logic. Exact refresh-token lifetime is a Supabase project setting, not application code, and
can be tuned operationally without a code change.

**Alternatives considered**: Custom long-lived static token — rejected, weakens security
posture and duplicates functionality Supabase already provides safely.

## 3. Row Level Security (RLS) Strategy

**Decision**: Every table that stores user- or project-scoped data (`projects`,
`conversations`, and later `documents`/`embeddings`) has RLS enabled with policies that
compare `auth.uid()` (Supabase's authenticated user id claim) against an `owner_id` column
(directly on `projects`, and transitively via a join/subquery to the parent project on
`conversations`).

**Rationale**: Constitution Principle I mandates authorization enforcement "at every
application and database layer" and explicitly calls out RLS. Enforcing isolation at the
database layer means even a bug in application-layer authorization cannot leak cross-tenant
data, satisfying FR-020.

**Alternatives considered**: Application-layer-only filtering (WHERE clauses in service
code) — rejected as the sole mechanism because it relies entirely on code correctness with no
defense-in-depth, violating the constitution's explicit RLS requirement.

## 4. Backend JWT Validation Approach

**Decision**: FastAPI dependency (`get_current_user`) extracts the `Authorization: Bearer
<jwt>` header, verifies the JWT signature against Supabase's project JWT secret (or JWKS for
asymmetric keys depending on Supabase project configuration), extracts `sub` (user id) and
expiry, and rejects the request with 401 on any failure. A second dependency
(`get_owned_project`) additionally validates that the path's `project_id` belongs to the
resolved user, returning 404 (not 403) to avoid disclosing existence of other users' projects
per FR-015 edge case.

**Rationale**: Centralizing JWT + ownership validation as reusable FastAPI dependencies
avoids duplicating security-critical logic across route handlers (constitution Principle IV:
avoid duplicated logic; Principle I: authorization at every layer).

**Alternatives considered**: Per-route manual checks — rejected due to duplication risk and
higher chance of an endpoint accidentally skipping a check.

## 5. Frontend Framework & PWA Setup

**Decision**: Next.js App Router (latest stable 14+), with a `manifest.ts` (or
`manifest.webmanifest`) for PWA installability, a service worker for offline app-shell
caching (via `next-pwa` or Next's built-in support), and a root `ThemeProvider` (e.g., built
on `next-themes` or a custom context) supporting `light`/`dark`/`system` modes applied at the
root layout so every route inherits theme + design-system tokens.

**Rationale**: App Router is required by the user's explicit instruction and is the current
Next.js standard for layouts/nested routing, which maps well to the
`app/(app)/projects/[projectId]/chat` structure needed for project-scoped navigation.

**Alternatives considered**: Pages Router — rejected, user explicitly specified App Router.

## 6. Apple Liquid Glass Design System Implementation

**Decision**: Implement a small set of reusable primitives (`GlassPanel`, `GlassCard`,
`GlassNavBar`, `GlassButton`) built with CSS (backdrop-filter blur + translucency + subtle
border/shadow tokens) and a shared design-tokens module (spacing scale, typography scale,
motion durations/easings) consumed via the theme provider so light/dark variants share the
same token names with different values.

**Rationale**: Constitution Principle VI requires a consistent design language "across every
screen, component, interaction, and state" with first-class light/dark support — a shared
token + primitive-component layer is the standard way to guarantee this consistency and avoid
each screen re-implementing glass effects ad hoc.

**Alternatives considered**: Per-page bespoke styling — rejected, would violate the
consistency requirement and create maintenance/duplication debt (Principle IV).

## 7. Conversation/Chat Data Modeling for This Slice

**Decision**: Model `conversations` as project-scoped rows (one active conversation "thread"
per project to start, extensible to multiple threads later) with a `messages` table for
individual turns; this slice implements creation of conversation threads and empty-state
chat UI, without wiring actual AI responses (which depend on the future RAG pipeline).

**Rationale**: Spec User Story 5 requires a "dedicated chat experience" scoped to the project
and an empty conversation state for new projects, but explicitly defers document
upload/retrieval; this means the chat UI and thread-creation endpoint must exist now, while
message generation logic is out of scope.

**Alternatives considered**: Deferring conversation modeling entirely to the RAG-pipeline
slice — rejected, since the spec explicitly requires the dedicated-chat navigation flow and
empty-state behavior as part of this foundation.
