import asyncio
import os
import shutil
from collections.abc import AsyncIterator
from pathlib import Path

from loguru import logger

DATA_DIR = Path(__file__).parent / "data"


def is_available() -> bool:
    return shutil.which("hermes") is not None


def get_version() -> str | None:
    if not is_available():
        return None
    try:
        result = __import__("subprocess").run(
            ["hermes", "--version"],
            capture_output=True, text=True, timeout=10,
        )
        text = (result.stdout or result.stderr or "").strip().splitlines()
        return text[0] if text else None
    except Exception:
        return None


def get_kanban_path() -> Path:
    return DATA_DIR / "hermes_kanban.db"


async def run_command(
    args: list[str], cwd: str | None = None, env: dict[str, str] | None = None
) -> tuple[int, str, str]:
    full_cmd = ["hermes", *args]
    logger.debug("hermes {}", " ".join(args))
    proc_env = {**os.environ}
    if env:
        proc_env.update(env)
    proc = await asyncio.create_subprocess_exec(
        *full_cmd,
        cwd=cwd or str(DATA_DIR),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=proc_env,
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode or 0, stdout.decode(), stderr.decode()


async def stream_run(args: list[str], cwd: str | None = None) -> AsyncIterator[str]:
    full_cmd = ["hermes", *args]
    logger.debug("hermes {} (streaming)", " ".join(args))
    proc = await asyncio.create_subprocess_exec(
        *full_cmd,
        cwd=cwd or str(DATA_DIR),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    async for raw in proc.stdout:
        line = raw.decode("utf-8", errors="replace").rstrip()
        if line:
            yield line
    await proc.wait()


SKILLS_SRC = Path(__file__).parent / "skills"
HERMES_SKILLS_DIR = Path.home() / ".hermes" / "skills"


def install_platform_skills() -> int:
    """Copy agent-os SKILL.md files to ~/.hermes/skills/.

    Returns number of skills installed (or 0 if Hermes not available).
    """
    if not SKILLS_SRC.is_dir():
        logger.debug("Skills source dir not found: {}", SKILLS_SRC)
        return 0
    installed = 0
    for skill_dir in SKILLS_SRC.iterdir():
        if not skill_dir.is_dir():
            continue
        src = skill_dir / "SKILL.md"
        if not src.exists():
            continue
        dst = HERMES_SKILLS_DIR / skill_dir.name / "SKILL.md"
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src.read_text())
        installed += 1
        logger.debug("Installed skill: {}", skill_dir.name)
    if installed:
        logger.info("Installed {} agent-os skills to {}", installed, HERMES_SKILLS_DIR)
    return installed


async def run_curator() -> tuple[int, str, str]:
    """Trigger a curator review cycle."""
    return await run_command(["curator", "run"])


async def init_kanban() -> bool:
    if not is_available():
        logger.info("Hermes not available — kanban init skipped")
        return False
    kanban_path = get_kanban_path()
    kanban_path.parent.mkdir(parents=True, exist_ok=True)
    code, out, err = await run_command(["kanban", "init"], cwd=str(DATA_DIR))
    if code != 0:
        logger.error("Hermes kanban init failed: {} {}", out, err)
        return False
    logger.info("Hermes kanban initialized at {}", kanban_path)
    return True
