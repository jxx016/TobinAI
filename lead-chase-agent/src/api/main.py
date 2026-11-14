"""ASGI app. The scheduler starts with the process unless SCHEDULER_ENABLED=false."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes import router
from src.api.scheduler import start_scheduler
from src.config import get_settings
from src.db.session import init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    settings = get_settings()
    init_db()
    scheduler = start_scheduler() if settings.scheduler_enabled else None
    logger.info(
        "lead chase api ready mock=%s llm=%s scheduler=%s",
        settings.mock_external_services,
        settings.llm_provider,
        scheduler is not None,
    )
    yield
    if scheduler is not None:
        scheduler.shutdown(wait=False)


app = FastAPI(title="Lead Chase Agent", version="0.1.0", lifespan=lifespan)
app.include_router(router)


def run() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )
