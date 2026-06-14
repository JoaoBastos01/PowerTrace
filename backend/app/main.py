"""FastAPI entry point for the PowerTrace backend."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.projects import router as projects_router
from app.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings.validate_security()
    init_db()
    yield


logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(levelname)s:%(name)s:%(message)s",
)

app = FastAPI(
    title="PowerTrace API",
    description=(
        "Procedural electrical floor-plan generation with persistent "
        "multi-user bearer authentication."
    ),
    version="0.4.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "version": "0.4.0"}
