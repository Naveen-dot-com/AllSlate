# Implementation Plan: Core Application Foundation

**Branch**: `001-core-foundation` | **Date**: 2026-08-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-core-foundation/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

Establish AllSlate's application foundation: Google OAuth sign-in via Supabase Auth, a
Next.js (App Router) PWA shell with an Apple Liquid Glass-inspired design system (light/dark
theme provider), a Supabase Postgres data model for Users/Projects/Conversations with
row-level security enforcing per-user and per-project isolation, and a FastAPI backend
exposing JWT-authenticated endpoints to create/list/switch projects and start conversation
threads. Document upload and the RAG pipeline are explicitly out of scope for this slice.

## Technical Context

**Language/Version**: TypeScript 5.x (frontend, Next.js 14+ App Router), Python 3.11+ (backend, FastAPI)

**Primary Dependencies**: Next.js, React 18+, Supabase JS client (`@supabase/ssr` /
`@supabase/supabase-js`), FastAPI, Pydantic v2, `supabase` Python client / `python-jose` (or
equivalent) for JWT validation, `next-pwa` (or Next.js native PWA/manifest + service worker
support) for installability

**Storage**: Supabase Postgres (Users/Profiles, Projects, Conversations tables), with
Row Level Security policies enforcing owner-scoped access

**Testing**: `pytest` (backend unit/integration, including RLS-policy and auth-dependency
tests), Vitest/Jest + React Testing Library (frontend component/unit tests), Playwright (or
equivalent) for end-to-end auth + project-switch flows

**Target Platform**: Web (installable PWA), served to modern evergreen browsers (desktop +
mobile), backend deployed as a containerized web service

**Project Type**: Web application (frontend + backend)

**Performance Goals**: Project switch reflects new chat context in <2s (SC-004); first-run
sign-in-to-first-project flow completes in <60s (SC-002); no specific backend throughput
target defined for this foundation slice beyond normal interactive API latency (<300ms p95
for project list/switch/create endpoints under nominal load)

**Constraints**: Must not block the UI during any auth or project operation (async-first per
constitution Principle V); all cross-project/cross-user data access MUST be denied at both API
and database layers (constitution Principle I); secrets/service credentials MUST never reach
the client bundle; light and dark mode MUST both be fully supported from this slice onward
(constitution Principle VI)

**Scale/Scope**: Single-tenant-per-user model scaling to many users, each with an unbounded
number of projects; this slice covers the navigation shell, auth, and project/chat data model
only — no document ingestion or retrieval pipeline

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Data Security & Tenant Isolation | Every project/conversation query MUST be scoped by authenticated user + project ownership at API layer AND enforced via Postgres RLS; JWT validated on every backend request; no secrets in frontend bundle; TLS in transit (Supabase + HTTPS deployment) | PASS — planned via Supabase RLS policies + FastAPI JWT dependency on all routes |
| II. Retrieval Accuracy & Source Fidelity | N/A for this slice — no document retrieval or RAG answer generation is in scope | PASS (not applicable) |
| III. End-to-End Observability | N/A for document pipeline stages in this slice; auth/session and project CRUD operations should still be logged for audit, but no multi-stage pipeline exists yet | PASS — basic structured logging planned for auth/project endpoints; full pipeline observability deferred to document-upload slice |
| IV. Code Quality & Type Safety | Backend = Python + FastAPI + Pydantic (per constraint); Frontend = TypeScript + Next.js (per constraint); unit/integration tests required before task completion | PASS — matches mandated stack exactly |
| V. Performance & Asynchronous Processing | Auth and project operations are lightweight CRUD, not long-running; no blocking UI operations planned; async FastAPI endpoints | PASS |
| VI. Consistent UX & Design System | Apple Liquid Glass-inspired design system with reusable glass-panel/blur components, shared theme provider, light + dark mode, applied app-wide (not just this slice) | PASS — explicit requirement of this plan |
| VII. Graceful Failure & Error Transparency | Auth failures, project creation failures, and ownership-check rejections must return clear, actionable errors without leaking existence of other users' data (per spec edge cases) | PASS — designed into FR-002 edge case handling and FR-015 (no existence disclosure) |
| VIII. Enterprise Readiness | Least-privilege JWT-scoped access, RLS as defense-in-depth, audit-friendly structured logs, no experimental shortcuts | PASS |

No violations requiring Complexity Tracking justification at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/001-core-foundation/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/
│   │   ├── deps.py          # Supabase JWT auth dependency, current-user/project resolution
│   │   └── routes/
│   │       ├── auth.py      # session/profile bootstrap endpoints (if needed beyond Supabase)
│   │       ├── projects.py  # create/list/switch project endpoints
│   │       └── conversations.py  # start/list conversation thread endpoints
│   ├── models/              # Pydantic schemas (Project, Conversation, UserProfile)
│   ├── services/            # business logic: project ownership checks, conversation creation
│   ├── db/                  # Supabase/Postgres client setup, RLS-aware query helpers
│   └── main.py               # FastAPI app entrypoint
├── migrations/                # SQL migrations: users/profiles, projects, conversations, RLS policies
└── tests/
    ├── contract/             # API contract tests (auth required, ownership enforcement)
    ├── integration/          # RLS + cross-user/cross-project isolation tests
    └── unit/

frontend/
├── app/                       # Next.js App Router
│   ├── (auth)/
│   │   └── sign-in/           # Google sign-in screen
│   ├── (app)/
│   │   ├── layout.tsx         # authenticated shell: nav, theme provider, project context
│   │   ├── projects/          # project list / create / switch UI
│   │   └── projects/[projectId]/
│   │       └── chat/          # project-scoped dedicated chat view
│   ├── layout.tsx              # root layout: PWA manifest, theme provider wiring
│   └── manifest.ts / manifest.webmanifest   # PWA manifest
├── components/
│   ├── design-system/          # Liquid Glass primitives: GlassPanel, GlassCard, buttons, nav, etc.
│   └── theme/                  # ThemeProvider (light/dark), theme toggle
├── lib/
│   ├── supabase/               # Supabase client (browser + server), auth helpers
│   └── api/                    # typed client for FastAPI endpoints
└── tests/
    ├── unit/
    └── e2e/                     # Playwright: sign-in, first-project onboarding, project switch, isolation UI checks
```

**Structure Decision**: Web application split into `backend/` (FastAPI + Pydantic, Supabase
Postgres access, JWT-validated REST API) and `frontend/` (Next.js App Router PWA with a shared
design-system component layer and theme provider applied at the root layout so light/dark and
Liquid Glass styling are available app-wide, not just within this feature's screens). This
matches constitution-mandated stack constraints (Principle IV) and keeps auth/session/project
concerns cleanly separated from the future document-upload and RAG-pipeline slices.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations — table intentionally left without entries.

