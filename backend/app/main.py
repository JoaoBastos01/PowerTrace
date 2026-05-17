"""Entry point FastAPI do PowerTrace backend."""

import logging
from fastapi import FastAPI

from app.config import settings
from app.api.v1.routes.floor_plan import router as floor_plan_router

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
)

app.include_router(floor_plan_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health_check():
    """Verifica se a API está no ar."""
    return {"status": "ok", "version": "0.1.0"}
