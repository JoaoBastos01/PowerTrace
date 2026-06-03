"""Entry point FastAPI do PowerTrace backend."""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.floor_plan import router as floor_plan_router
from app.api.v1.routes.projects import router as projects_router
from app.config import settings
from app.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    init_db()
    yield

# ── Logging ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(levelname)s:%(name)s:%(message)s",
)

# ── Aplicação ────────────────────────────────────────────────────────
app = FastAPI(
    title="PowerTrace API",
    description="Geração procedural de plantas baixas elétricas conforme NBR 5410/8995.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(floor_plan_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health_check():
    """Verifica se a API está no ar."""
    return {"status": "ok", "version": "0.1.0"}

