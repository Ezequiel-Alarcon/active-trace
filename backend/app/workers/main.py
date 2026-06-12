"""Worker entrypoint — starts the comunicacion poll loop."""

from __future__ import annotations

import asyncio
import logging

from app.core.config import get_settings
from app.workers.comunicacion_worker import run_poll_loop

logger = logging.getLogger("activia_trace.worker")


async def run_worker() -> None:
    settings = get_settings()
    logger.info("Starting comunicacion worker...")

    retry_count = 0
    max_retries = 5

    while retry_count < max_retries:
        try:
            await run_poll_loop()
        except Exception as exc:
            retry_count += 1
            wait_time = min(2**retry_count, 30)
            logger.warning(
                "Worker crashed (attempt %s/%s): %s. Retrying in %ss...",
                retry_count,
                max_retries,
                exc,
                wait_time,
            )
            await asyncio.sleep(wait_time)

    logger.error("Worker exhausted retry attempts. Exiting.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_worker())