import asyncio
import os

from loguru import logger

from .cron_adapter import tick
from .hermes_adapter import is_available

TICK_INTERVAL_SECONDS = int(os.environ.get("PLATFORM_CRON_TICK_INTERVAL", "30"))
_task = None


async def _safe_tick() -> None:
    try:
        code, out, err = await tick(accept_hooks=True)
        if code != 0 and err:
            logger.debug("Cron tick non-zero exit ({}): {}", code, err.strip()[:200])
    except Exception as exc:
        logger.error("Cron tick exception: {}", exc)


async def _loop() -> None:
    logger.info("Platform cron ticker started (interval={}s)", TICK_INTERVAL_SECONDS)
    while True:
        await _safe_tick()
        await asyncio.sleep(TICK_INTERVAL_SECONDS)


def start() -> asyncio.Task | None:
    if not is_available():
        return None
    if os.environ.get("DISABLE_PLATFORM_CRON", "").lower() in ("1", "true", "yes"):
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
