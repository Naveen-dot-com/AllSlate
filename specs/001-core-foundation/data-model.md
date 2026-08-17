# Data Model: Core Application Foundation

## Entity: `user_profiles`

Represents an authenticated AllSlate user, mirroring (and extending) the Supabase Auth user.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | `uuid` | PK, references `auth.users.id` | Same id as Supabase Auth user (1:1) |
| `email` | `text` | NOT NULL | Copied from Google profile at first sign-in |
| `display_name` | `text` | NULL | From Google profile, optional |
| `avatar_url` | `text` | NULL | From Google profile, optional |
| `created_at` | `timestamptz` | NOT NULL, default `now()` | First sign-in time |
| `last_seen_at` | `timestamptz` | NOT NULL, default `now()` | Updated on each session refresh |

**Relationships**: One `user_profiles` row owns zero or more `projects`.

**Validation rules**: Row created idempotently on first Supabase Auth sign-in (upsert on
`id`) to satisfy FR-002 (create-or-retrieve, no duplicates).

**RLS policy**: A user may `SELECT`/`UPDATE` only the row where `id = auth.uid()`.

---

## Entity: `projects`

The primary organizational and isolation boundary.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | `uuid` | PK, default `gen_random_uuid()` | Unique project identifier (FR-013) |
| `owner_id` | `uuid` | NOT NULL, FK → `user_profiles.id` | Enforces single-owner rule (FR-013) |
| `name` | `text` | NOT NULL, length 1–200 | Required project name |
| `description` | `text` | NULL, length ≤ 2000 | Optional description/summary |
| `created_at` | `timestamptz` | NOT NULL, default `now()` | |
| `updated_at` | `timestamptz` | NOT NULL, default `now()` | Updated on name/description edit |

**Relationships**: Belongs to exactly one `user_profiles` row (`owner_id`). Has many
`conversations`.

**Validation rules**:
- `name` must be non-empty after trimming whitespace (edge case: empty name rejected).
- `description` may be empty/null but not exceed max length (edge case: overlong input
  rejected with a clear validation error).

**RLS policy**: A user may `SELECT`/`INSERT`/`UPDATE`/`DELETE` only rows where
`owner_id = auth.uid()`.

**State/behavior notes**: No project deletion UI is required by this spec (Assumptions), but
the RLS policy and schema still support delete for administrative/future use without extra
migration work.

---

## Entity: `conversations`

A project-scoped chat context.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | `uuid` | PK, default `gen_random_uuid()` | |
| `project_id` | `uuid` | NOT NULL, FK → `projects.id` (`ON DELETE CASCADE`) | Isolation boundary (FR-017) |
| `title` | `text` | NULL | Optional, may be auto-generated later |
| `created_at` | `timestamptz` | NOT NULL, default `now()` | |
| `updated_at` | `timestamptz` | NOT NULL, default `now()` | Updated on new message |

**Relationships**: Belongs to exactly one `projects` row. Has many `messages`.

**RLS policy**: A user may access a `conversations` row only if the referenced `projects.id`
has `owner_id = auth.uid()` (implemented via a policy using an `EXISTS` subquery against
`projects`, or a denormalized `owner_id` column kept in sync via trigger — decision deferred
to implementation task, either approach satisfies FR-017/FR-018).

---

## Entity: `messages`

A single turn within a conversation.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | `uuid` | PK, default `gen_random_uuid()` | |
| `conversation_id` | `uuid` | NOT NULL, FK → `conversations.id` (`ON DELETE CASCADE`) | |
| `role` | `text` | NOT NULL, CHECK IN (`'user'`, `'assistant'`, `'system'`) | |
| `content` | `text` | NOT NULL | Message text; RAG-grounded content generation is out of scope for this slice |
| `created_at` | `timestamptz` | NOT NULL, default `now()` | |

**Relationships**: Belongs to exactly one `conversations` row (transitively one project).

**RLS policy**: Same pattern as `conversations` — access requires the transitive owning
project's `owner_id = auth.uid()`.

**Note**: This slice only needs to support creating/listing empty conversation threads (per
spec User Story 5); actual assistant-generated `content` values depend on the future RAG
pipeline slice and are not populated here.

---

## Cross-Cutting Isolation Rule (applies to all tables above except `user_profiles`)

Every query MUST be scoped by both:
1. The authenticated user's identity (via Supabase JWT `auth.uid()` at the DB layer, and the
   FastAPI-resolved current user at the API layer), and
2. The target project's identity (`project_id` / transitive project ownership).

This dual-scoping is enforced redundantly at the API layer (FastAPI dependencies) and the
database layer (RLS policies), per constitution Principle I and FR-014–FR-020.
