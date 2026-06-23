"""CrisisNet FastAPI Application.

Research Prototype — Not a real crisis service.
For demonstration purposes only, using synthetic test data.
"""

import structlog
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.websockets import router as ws_router
from app.db.database import engine, Base

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: create tables on startup, dispose engine on shutdown."""
    logger.info("starting_crisisnet", version=settings.VERSION)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database_tables_created")
    yield
    await engine.dispose()
    logger.info("shutdown_complete")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Research Prototype — Not a real crisis service. "
        "Multi-agent crisis triage pipeline using LangGraph."
    ),
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──
app.include_router(ws_router, tags=["WebSockets"])


# ── Health Check ──


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "disclaimer": "Research prototype — synthetic data only",
    }
