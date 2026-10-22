# Changelog

## 1.1.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.0.0 — work-in-progress checkpoint

Issue tracker feature implemented. All backend and frontend tests pass.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-22

### Added
- Rust tracking issue dashboard with 8 built-in tracking issues (specialization, extern types, pointer metadata, secure random, impl trait in type aliases, ascii::Char, int_roundings, coroutines)
- GitHub issue sync endpoint (`POST /api/v1/issues/sync`) fetches and stores issues with comments
- Issue list API with pagination, filtering by state/search/label (`GET /api/v1/issues`)
- Issue detail API with full comments (`GET /api/v1/issues/{id}`)
- AI-powered issue analysis endpoint (`POST /api/v1/issues/{id}/analyze`) with multi-provider LLM support (OpenAI-compatible, Anthropic, Gemini, Ollama)
- Analysis history storage and retrieval (`GET /api/v1/issues/{id}/analyses`)
- Frontend issue list with filtering (state, search, label), sorting, and pagination
- Frontend issue detail view with body, comments, and AI analysis display
- Advisory labeling on all AI-generated content
- Three complete workflows: browse issues, search/filter issues, analyze issue with AI
- 8 backend tests covering sync, pagination, filtering, detail, analysis, and LLM client behavior
- Frontend tests for issue list loading, error states, and empty states

### Security
- LLM API keys only used server-side, never exposed to frontend
- LLM provider errors surfaced clearly without fabricating successful responses
- AI analysis opt-in only, requires explicit LLM_API_KEY configuration

## [1.0.0] - 2025-10-15

### Added
- FastAPI backend with health check endpoint (`/health`)
- React + TypeScript + Vite frontend with health display
- Docker Compose orchestration for backend and frontend
- GitHub Actions CI workflow (backend tests, frontend tests, Docker builds)
- SQLite database with SQLAlchemy async ORM
- Configuration management with Pydantic Settings
- Basic project structure: backend/app/{api,services,models,core}, frontend/src
- Backend tests with pytest + httpx
- Frontend tests with Vitest + React Testing Library
- Non-root Dockerfiles for both services
- README with architecture, API reference, and AI/ML evaluation section
- MIT License
- Portfolio metadata (portfolio.json)

### Security
- Demo mode restricted to localhost
- No hardcoded credentials
- OIDC-ready configuration structure
