# Changelog

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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