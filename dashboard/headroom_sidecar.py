import asyncio
import os
import shutil

from loguru import logger

HEADROOM_PORT = int(os.environ.get("HEADROOM_PORT", "8787"))
HEADROOM_HOST = os.environ.get("HEADROOM_HOST", "127.0.0.1")
PROXY_URL = f"http://{HEADROOM_HOST}:{HEADROOM_PORT}"

_proc: asyncio.subprocess.Process | None = None


def is_available() -> bool:
    return shutil.which("headroom") is not None


def proxy_url() -> str:
    return PROXY_URL


async def start() -> bool:
    global _proc
    if not is_available():
        logger.info("headroom not found on PATH — skipping proxy sidecar")
        return False

    if _proc is not None and _proc.returncode is None:
        logger.debug("Headroom proxy already running")
        return True

    cmd = [
        "headroom", "proxy",
        "--port", str(HEADROOM_PORT),
        "--host", HEADROOM_HOST,
    ]

    proc_env = {**os.environ}
    proc_env.setdefault("HEADROOM_STATELESS", "true")

    logger.info("Starting Headroom proxy on {}:{}", HEADROOM_HOST, HEADROOM_PORT)
    try:
        _proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=proc_env,
        )
    except FileNotFoundError:
        logger.warning("headroom binary not found — proxy sidecar disabled")
        return False

    await asyncio.sleep(1)

    if _proc.returncode is not None:
        _, stderr = await _proc.communicate()
        logger.error("Headroom proxy exited immediately: {}", stderr.decode() if stderr else "unknown")
        _proc = None
        return False

    logger.info("Headroom proxy started (PID {}) — listening on {}", _proc.pid, PROXY_URL)
    return True


async def stop() -> None:
    global _proc
    if _proc is not None and _proc.returncode is None:
        logger.info("Stopping Headroom proxy (PID {})", _proc.pid)
        _proc.terminate()
        try:
            await asyncio.wait_for(_proc.wait(), timeout=5)
        except TimeoutError:
            logger.warning("Headroom proxy did not terminate in time, killing")
            _proc.kill()
            await _proc.wait()
        _proc = None
