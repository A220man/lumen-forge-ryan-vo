# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

issue-tracker

## Roadmap

### skeleton — FastAPI/React skeleton with health check

Status: done

Acceptance:
- Backend FastAPI app starts and serves /health endpoint
- Frontend React+Vite+TypeScript app builds and loads
- Docker Compose brings up both services
- Backend tests pass (pytest)
- Frontend tests pass (vitest)
- CI workflow runs both test suites

Implementation: `backend/app/main.py`, `backend/requirements.txt`, `backend/Dockerfile`, `backend/tests/test_health.py`, `frontend/package.json`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/Dockerfile`, `frontend/vite.config.ts`, `compose.yaml`, `.github/workflows/ci.yml`

Tests: `backend/tests/test_health.py`, `frontend/src/App.test.tsx`

### issue-tracker — Rust issue tracking dashboard with AI analysis

Status: done

Acceptance:
- Backend stores and serves Rust tracking issues from GitHub
- Frontend displays issue list with filtering/sorting
- AI-powered issue summarization endpoint (opt-in, labeled advisory)
- Three workflows: browse, search, analyze issue
- Persistent SQLite storage with pagination

Implementation: `backend/app/models/issue.py`, `backend/app/api/issues.py`, `backend/app/services/github_sync.py`, `backend/app/services/ai_analysis.py`, `backend/app/core/database.py`, `backend/app/core/config.py`, `backend/tests/test_issues.py`, `frontend/src/api/client.ts`, `frontend/src/components/IssueList.tsx`, `frontend/src/components/IssueDetail.tsx`, `frontend/src/App.tsx`, `frontend/src/index.css`

Tests: `backend/tests/test_issues.py`, `frontend/src/App.test.tsx`

### auth-oidc — OIDC authentication with Keycloak

Status: planned

Acceptance:
- Keycloak realm configured via compose
- Backend validates JWT tokens with roles
- Frontend PKCE login flow with sessionStorage
- Protected API endpoints require authentication
- Demo mode for local development only

Implementation: `backend/app/core/auth.py`, `backend/app/api/auth.py`, `frontend/src/auth/`, `compose.yaml (Keycloak service)`, `realm-export.json`

Tests: `backend/tests/test_auth.py`, `frontend/src/auth/AuthProvider.test.tsx`

### docs-packaging — Documentation, packaging, and portfolio metadata

Status: done

Acceptance:
- README with architecture diagram and install steps
- CHANGELOG with actual changes
- portfolio.json at root
- LICENSE MIT
- pyproject.toml with author metadata
- .env.example with blank credentials
- .gitignore

Implementation: `README.md`, `CHANGELOG.md`, `portfolio.json`, `LICENSE`, `pyproject.toml`, `.env.example`, `.gitignore`

