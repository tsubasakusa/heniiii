"""Lightweight in-process scheduler (no external dependency).

Periodically publishes crossword puzzles whose scheduled date has arrived, so a
daily puzzle set to `scheduled` for a future date auto-goes-live. Runs once at
startup (to catch up after a date rollover / restart) and then hourly.
"""
import asyncio
import logging
from datetime import date

from app.database import AsyncSessionLocal
from app.services.game_service import GameService

logger = logging.getLogger("heniiii.scheduler")
_service = GameService()

DEFAULT_INTERVAL_SECONDS = 3600


async def promote_once() -> int:
    async with AsyncSessionLocal() as db:
        promoted = await _service.promote_scheduled(db, date.today())
    if promoted:
        logger.info("Published %d scheduled crossword puzzle(s)", promoted)
    return promoted


async def run_scheduler(
    stop: asyncio.Event, interval_seconds: int = DEFAULT_INTERVAL_SECONDS
) -> None:
    while not stop.is_set():
        try:
            await promote_once()
        except Exception:  # never let a transient error kill the loop
            logger.exception("Scheduler tick failed")
        try:
            await asyncio.wait_for(stop.wait(), timeout=interval_seconds)
        except asyncio.TimeoutError:
            pass  # interval elapsed -> next tick
