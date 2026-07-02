import asyncio
import os

from loguru import logger

from dashboard.hermes_adapter import is_available, run_curator

CURATOR_INTERVAL_HOURS = int(os.environ.get("HERMES_CURATOR_INTERVAL_HOURS", "24"))
_task = None


async def _safe_run() -> None:
    try:
        code, out, err = await run_curator()
        if code != 0 and err:
            logger.warning("Curator run exited {}: {}", code, err.strip()[:300])
        else:
            logger.debug("Curator run completed")
    except Exception as exc:
        logger.error("Curator run exception: {}", exc)


async def _loop() -> None:
    logger.info("Hermes curator loop started (interval={}h)", CURATOR_INTERVAL_HOURS)
    await asyncio.sleep(120)
    while True:
        await _safe_run()
        await asyncio.sleep(CURATOR_INTERVAL_HOURS * 3600)


def start() -> asyncio.Task | None:
    if not is_available():
        return None
    if os.environ.get("DISABLE_HERMES_CURATOR", "").lower() in ("1", "true", "yes"):
        return None
    global _task
    if _task is not None and not _task.done():
        return _task
    _task = asyncio.create_task(_loop())
    return _task


def stop() -> None:
    global _task
    if _task is not None:
        _task.cancel()
        _task = None
