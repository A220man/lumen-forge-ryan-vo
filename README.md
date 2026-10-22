# lumen-forge-ryan-vo — Ryan Vo

> Work in progress. This checkpoint may be incomplete or fail tests. See PLAN.md and STATUS.md before use.


**Ryan Vo | AI & Machine Learning**

An AI/ML developer tool for tracking, analyzing, and understanding Rust compiler tracking issues with intelligent summarization and workflow support.

## Problem

Rust compiler tracking issues (like specialization, extern types, pointer metadata, coroutines, etc.) are complex, long-running discussions spanning years with hundreds of comments. Developers and contributors need a way to quickly understand the current state, unresolved questions, and implementation progress without reading through entire issue threads.

## Approach

This application provides:
- **Structured issue tracking**: Fetches and stores Rust tracking issues from GitHub with full metadata
- **AI-powered summarization**: Optional LLM-based analysis that generates concise summaries of issue status, blockers, and key decisions (opt-in, labeled advisory)
- **Three core workflows**: Browse issues with filtering/sorting, search by keywords/labels, and deep-dive analysis with AI assistance
- **Persistent storage**: SQLite backend with full pagination, filtering, and audit logging

## Architecture

```mermaid
graph TD
    A[Frontend: React + TypeScript + Vite] -->|HTTP/JSON| B[Backend: FastAPI + Python]
    B --> C[(SQLite Database)]
    B --> D[GitHub API]
    B --> E[LLM Provider (Optional)]
    F[Keycloak OIDC] --> B
    F --> A
```

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Or: Python 3.12, Node 24, SQLite

### Development (Docker Compose)
```bash
# Start all services
docker compose up --build

# Backend: http://127.0.0.1:8000
# Frontend: http://127.0.0.1:3000
# Health: http://127.0.0.1:8000/health
```

### Development (Local)
```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## Configuration

Copy `.env.example` to `.env` and configure:

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | SQLite connection string | Yes (default: `sqlite+aiosqlite:///./data/app.db`) |
| `DEBUG` | Enable debug mode | No (default: false) |
| `LLM_API_KEY` | API key for LLM provider | No (enables AI features) |
| `LLM_PROVIDER` | Provider type: `openai-compatible`, `anthropic`, `gemini`, `ollama` | No |
| `LLM_MODEL` | Model name | No |
| `LLM_BASE_URL` | Custom base URL (for Ollama/LiteLLM) | No |
| `OIDC_ISSUER_URL` | Keycloak realm URL | No (enables auth) |
| `OIDC_CLIENT_ID` | OIDC client ID | No |
| `OIDC_CLIENT_SECRET` | OIDC client secret | No |

## API Reference

### Health
- `GET /health` - Service health check

### Issues (Planned)
- `GET /api/v1/issues` - List issues with pagination/filtering
- `GET /api/v1/issues/{id}` - Get issue details
- `POST /api/v1/issues/sync` - Sync from GitHub
- `POST /api/v1/issues/{id}/analyze` - AI analysis (opt-in)

### Authentication (Planned)
- `GET /api/v1/auth/login` - Initiate OIDC login
- `GET /api/v1/auth/callback` - OIDC callback
- `POST /api/v1/auth/logout` - Logout

## AI/ML Evaluation

This product includes an **AI-powered issue analysis feature** (planned) that uses LLMs to generate structured summaries of Rust tracking issues.

### Reproducible Baseline
```bash
# With LLM_API_KEY configured
curl -X POST http://localhost:8000/api/v1/issues/31844/analyze \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
```

### Data Provenance
- Source: GitHub Issues API (rust-lang/rust repository)
- Tracking issues with `tracking-issue` label or specific issue numbers
- Full issue body, comments, and metadata stored locally

### Limitations
- LLM responses are **advisory only** - labeled as such in UI
- Grounded in actual stored issue data, not hallucinated
- Provider errors surface clearly (no fabricated successes)
- Works fully offline without LLM key (core features)

## Security Limitations

- Demo mode binds to `127.0.0.1` only - refuses to start in production without proper OIDC config
- No hardcoded credentials or bypasses
- Tokens never logged
- SQLite for development; PostgreSQL recommended for production
- HTTPS/TLS termination required at reverse proxy (not included)

## Provider Configuration

| Provider | Base URL | Notes |
|----------|----------|-------|
| OpenAI | `https://api.openai.com/v1` | Default |
| Anthropic | `https://api.anthropic.com` | Messages API |
| Gemini | `https://generativelanguage.googleapis.com` | generateContent |
| Ollama | `http://localhost:11434/v1` | OpenAI-compatible |
| LiteLLM | Configurable | OpenAI-compatible proxy |
| OpenRouter | `https://openrouter.ai/api/v1` | OpenAI-compatible |

## SSO/SAML Setup

Keycloak supports upstream SAML IdPs through identity brokering:
1. Configure SAML IdP in Keycloak Admin Console → Identity Providers
2. Set up attribute mapping (email, name, roles)
3. Test brokered login flow
4. Map IdP groups to realm roles (viewer, operator, admin)

See Keycloak documentation for detailed SAML broker setup.

## License

MIT License - Copyright (c) 2025 Ryan Vo <ryandtvo@gmail.com>