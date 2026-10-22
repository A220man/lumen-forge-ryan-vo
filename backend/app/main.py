from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown (cleanup if needed)


def create_app() -> FastAPI:
    app = FastAPI(
        title="lumen-forge-ryan-vo",
        version="1.0.0",
        description="AI/ML developer tool for tracking and analyzing Rust compiler issues",
        lifespan=lifespan,
    )

    # CORS for frontend development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["health"])
    async def health_check():
        return {"status": "ok", "service": "lumen-forge-ryan-vo", "version": "1.0.0"}

    # API routes
    from app.api import issues
    app.include_router(issues.router, prefix="/api/v1")

    return app


app = create_app()