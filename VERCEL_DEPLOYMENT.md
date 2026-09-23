# Vercel deployment setup for AllSlate

This app has two runtime pieces:

1. The Next.js frontend in [frontend](frontend)
2. The FastAPI backend in [backend](backend)

The app is already configured to read the deployment variables from environment settings, and the backend accepts both the standard names and Vercel-friendly aliases.

## Required environment variables

### Frontend (Vercel project)

Set these in the Vercel project for the frontend app:

- `ALLSLATE_API_URL` = `https://your-backend-domain.example.com`
- `NEXT_PUBLIC_ALLSLATE_API_URL` = `https://your-backend-domain.example.com`
- `NEXT_PUBLIC_SUPABASE_URL` = `https://<project-ref>.supabase.co`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` = `<supabase-anon-key>`

Optional but useful for parity in a single Vercel app environment:

- `SUPABASE_URL` = `https://<project-ref>.supabase.co`
- `SUPABASE_ANON_KEY` = `<supabase-anon-key>`

### Backend (separate deployed API or Vercel serverless backend)

Set these in the environment where the FastAPI service is running:

- `CORS_ORIGINS` = `https://your-app.vercel.app`
- `GEMINI_API_KEY` = `<gemini-api-key>`
- `GOOGLE_API_KEY` = `<gemini-api-key>`
- `SUPABASE_URL` = `https://<project-ref>.supabase.co`
- `SUPABASE_ANON_KEY` = `<supabase-anon-key>`
- `SUPABASE_SERVICE_ROLE_KEY` = `<supabase-service-role-key>`
- `DATABASE_URL` = `postgresql://postgres:<password>@db.<project-ref>.supabase.co:5432/postgres`
- `WEB_SEARCH_API_KEY` = `<optional-web-search-key>`
- `EXA_API_KEY` = `<optional-web-search-key>`

## Supabase wiring

The backend uses Supabase in [backend/app/services/providers.py](backend/app/services/providers.py) by reading the following values in order:

- `SUPABASE_URL` or `NEXT_PUBLIC_SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_ANON_KEY`, or `NEXT_PUBLIC_SUPABASE_ANON_KEY`

The frontend should use the public client values:

- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

Do not expose `SUPABASE_SERVICE_ROLE_KEY` in the browser or client-side code.

## Gemini wiring

The backend checks for Gemini in this order:

- `GEMINI_API_KEY`
- `GOOGLE_API_KEY`
- `GOOGLE_GENERATIVE_AI_API_KEY`

These keys are then used by the generator invoked in [backend/app/api/routes/chat.py](backend/app/api/routes/chat.py).

If no Gemini key is configured, the app falls back to a local deterministic answer instead of failing the request.

## Recommended deployment pattern

Recommended production setup:

- Frontend: Next.js on Vercel
- Backend: FastAPI on a separate host (Railway, Render, Fly, Azure, or a Vercel serverless backend if you later move the API)
- Data: Supabase Postgres + Auth
- AI: Gemini API key
- Web search: optional, only if you enable that feature later

This keeps the browser-facing frontend simple while allowing the FastAPI backend to keep the service-role key and database access private.

## Files to keep in sync

- [frontend/.env.example](frontend/.env.example)
- [backend/.env.example](backend/.env.example)
- [frontend/next.config.mjs](frontend/next.config.mjs)
- [backend/app/services/providers.py](backend/app/services/providers.py)

## Example Vercel settings

For the frontend project in Vercel, set:

```
ALLSLATE_API_URL=https://your-backend-domain.example.com
NEXT_PUBLIC_ALLSLATE_API_URL=https://your-backend-domain.example.com
NEXT_PUBLIC_SUPABASE_URL=https://<project-ref>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<supabase-anon-key>
```

For the backend environment, set:

```
CORS_ORIGINS=https://your-app.vercel.app
GEMINI_API_KEY=<gemini-api-key>
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_ANON_KEY=<supabase-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<supabase-service-role-key>
DATABASE_URL=postgresql://postgres:<password>@db.<project-ref>.supabase.co:5432/postgres
```
