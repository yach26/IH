"""
AgroTwin FastAPI service.

Run from agrotwin_api/:
    uvicorn app.main:app --reload

Env:
    AGROTWIN_DB  path to SQLite twin (default ./agrotwin.db)
    DATABASE_URL  Postgres connection string (overrides SQLite)
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .agents.monitoring_agent import get_monitoring_agent, register_all_handlers
from .api.routes import router
from .core.event_bus import get_bus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
LOG = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    LOG.info("Kisan Saathi API starting up...")
    LOG.info("Database: %s", os.environ.get("DATABASE_URL", "SQLite"))
    register_all_handlers()
    get_monitoring_agent()
    get_bus()
    LOG.info("Kisan Saathi API ready")
    yield
    LOG.info("Kisan Saathi API shutting down")


app = FastAPI(
    title="Kisan Saathi",
    description=(
        "Proof-carrying fertilizer recommendations. "
        "kg/ha originate only from the Nutrient Ledger heuristic "
        "(DAP→Urea→MOP), never from an LLM."
    ),
    version="0.2.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
