# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CV Maker is a full-stack job application tracking system with:
- **Backend**: FastAPI (Python) API server with SQLAlchemy ORM
- **Database**: PostgreSQL with `cv_maker_db` database
- **Frontend**: React with TypeScript + Vite + TailwindCSS
- **AI Features**: URL parsing with web scraping + Claude AI / Gemini AI integration

## Running the Application

### Docker (recommended)

```bash
cp .env.docker .env          # first time only — add your API keys
docker compose up --build    # first run
docker compose up            # subsequent runs
```

- App: http://localhost:82
- API docs: http://localhost:8192/docs

The compose stack has three services: `db` (Postgres 16), `backend` (FastAPI on port 8192), `frontend` (nginx on port 82 proxying `/api/` → backend).

**Environment variables** — edit `.env` (copied from `.env.docker`):
- `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` — AI features (optional, features degrade gracefully)
- `LINKEDIN_LI_AT` — LinkedIn scraping cookie (optional)
- `DISABLE_AUTH=true` — default; set to `false` + add `AUTH_PASSWORD_HASH` for shared deployments
- `POSTGRES_PASSWORD` — change for non-local deployments

**Database**: the Docker Postgres volume is separate from any local Postgres instance. Starting fresh is expected; to migrate existing data: `pg_dump --data-only -U <local-user> cv_maker_db | docker compose exec -T db psql -U postgres -d cv_maker_db`

### Local development (without Docker)

```bash
# Terminal 1 — backend
source .venv/bin/activate
cd backend && uvicorn main:app --reload --port 8192

# Terminal 2 — frontend
cd frontend && npm run dev
```

- Frontend: http://localhost:5173
- API: http://127.0.0.1:8192
- API docs: http://127.0.0.1:8192/docs

Requires a local Postgres instance with `cv_maker_db` database (connection string configurable via `DATABASE_URL` env var, defaults to `postgresql://filipe@localhost/cv_maker_db`).

## Development Environment

### Python
- **Package manager**: `uv` — always use `uv add <pkg>` (never pip)
- **Python version**: 3.13
- **Virtual environment**: `.venv/` (managed by uv)

### Frontend
- **Framework**: React 19 + TypeScript (strict + `verbatimModuleSyntax` + `erasableSyntaxOnly`)
- **Build tool**: Vite 7
- **Styling**: TailwindCSS 4
- **HTTP client**: Axios — all calls go through `frontend/src/services/api.ts`
- TypeScript note: use `import type` for type-only imports; `enum` is banned by `erasableSyntaxOnly` — use `as const` objects instead

### Database schema
Managed by `docker/init.sql` (authoritative for Docker) and SQLAlchemy `Base.metadata.create_all()` (creates base tables on startup). Migrations in `backend/migrations/` extend the schema and are idempotent (`IF NOT EXISTS`).

Key tables: `jobs`, `lego_blocks`, `generated_cvs`, `generated_cover_letters`, `contact_history`, `tax_configs`

The `application_status` enum is created explicitly in `init.sql` because the SQLAlchemy model uses `create_type=False`.

## Common Commands

### Backend
```bash
uv add <package>                          # install dependency
cd backend && uvicorn main:app --reload   # dev server (port 8192)
```

### Frontend
```bash
cd frontend && npm run dev     # dev server (port 5173)
cd frontend && npm run build   # production build
cd frontend && npm run lint    # lint
```

### Docker
```bash
docker compose up --build      # build and start
docker compose down            # stop
docker compose down -v         # stop and delete volumes (wipes DB)
docker compose logs backend    # tail logs for a service
```

### Database (local)
```bash
psql -d cv_maker_db                                    # connect
psql -d cv_maker_db -f backend/migrations/001_add_jobhunt_tables.sql  # run a migration
```

## Code Architecture

### Backend structure

| File | Purpose |
|---|---|
| `backend/main.py` | FastAPI app, all routes |
| `backend/database.py` | SQLAlchemy engine; reads `DATABASE_URL` env var |
| `backend/models.py` | ORM models (`Job`, `LegoBlock`, `GeneratedCV`, etc.) |
| `backend/schemas.py` | Pydantic request/response schemas |
| `backend/crud.py` | DB CRUD operations |
| `backend/job_parser.py` | AI-powered job URL scraping + parsing |
| `backend/auth.py` | HTTP Basic auth (`DISABLE_AUTH=true` skips it) |
| `backend/tax_calculator.py` | UK salary/tax calculations |
| `backend/lego_blocks_matcher.py` | Gemini AI matching of job requirements to CV blocks |

### API endpoints (port 8192)

- `GET /jobs` — list with `?status=`, `?company=`, `?skip=`, `?limit=`
- `POST /jobs` — create
- `GET|PUT|DELETE /jobs/{id}` — read/update/delete
- `POST /parse-job-url` — scrape and AI-parse a job posting
- `POST /calculate-salary` — UK net salary calculation
- `GET /jobs/{id}/match-cv-blocks` — Gemini AI CV block matching
- `POST /jobs/{id}/generate-cv` — generate CV from lego blocks
- `POST /jobs/{id}/generate-cover-letter` — AI cover letter
- `GET /jobs/{id}/contact-history`, `POST /jobs/{id}/contact-history`
- `GET /health` — health check (no auth)

### Frontend structure

| File | Purpose |
|---|---|
| `frontend/src/App.tsx` | Root component, routing state |
| `frontend/src/components/JobList.tsx` | Job cards + filters |
| `frontend/src/components/JobForm.tsx` | Create/edit form |
| `frontend/src/components/JobView.tsx` | Detailed job view |
| `frontend/src/services/api.ts` | Axios client; reads `VITE_API_URL` (default `/api` in Docker, `http://127.0.0.1:8192` locally) |
| `frontend/src/types/job.ts` | TypeScript types (`ApplicationStatus` as `as const` object) |

### Docker files

| File | Purpose |
|---|---|
| `docker-compose.yml` | Service definitions |
| `backend/Dockerfile` | Python 3.13-slim + pip + Playwright/Chromium |
| `backend/entrypoint.sh` | Waits for Postgres, then starts uvicorn |
| `frontend/Dockerfile` | Multi-stage: Vite build → nginx |
| `frontend/nginx.conf` | Serves SPA; proxies `/api/*` → `http://backend:8192/*` |
| `docker/init.sql` | Full Postgres schema (runs once on fresh volume) |
| `.env.docker` | Environment variable template |
| `.dockerignore` | Excludes `.venv`, `node_modules`, secrets |
