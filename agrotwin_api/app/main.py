"""
AgroTwin FastAPI service.

Run from agrotwin_api/:
    uvicorn app.main:app --reload

Env:
    AGROTWIN_DB  path to SQLite twin (default ./agrotwin.db)
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .agents.monitoring_agent import get_monitoring_agent, register_all_handlers
from .api.routes import router
from .core.event_bus import get_bus


@asynccontextmanager
async def lifespan(app: FastAPI):
    register_all_handlers()
    get_monitoring_agent()
    get_bus()
    yield


app = FastAPI(
    title="AgroTwin AI",
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
