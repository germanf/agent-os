import asyncio
import os
import shutil

from loguru import logger

LEARN_INTERVAL_HOURS = int(os.environ.get("HEADROOM_LEARN_INTERVAL_HOURS", "168"))  # 7 days
_task = None


async def _run_learn() -> None:
    binary = shutil.which("headroom")
    if not binary:
        logger.debug("headroom CLI not found — skipping learn")
        return
    logger.info("Running headroom learn...")
    proc = await asyncio.create_subprocess_exec(
        binary, "learn",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode == 0:
        logger.info("headroom learn completed successfully")
    else:
        logger.warning("headroom learn exited {}: {}", proc.returncode, stderr.decode()[:500] if stderr else "")


async def _loop() -> None:
    logger.info("Headroom learn loop started (interval={}h)", LEARN_INTERVAL_HOURS)
    await asyncio.sleep(60)  # delay first run to let system stabilize
    while True:
        await _run_learn()
        await asyncio.sleep(LEARN_INTERVAL_HOURS * 3600)


def start() -> asyncio.Task | None:
    if os.environ.get("DISABLE_HEADROOM_LEARN", "").lower() in ("1", "true", "yes"):
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
