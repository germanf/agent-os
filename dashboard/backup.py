import asyncio
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from loguru import logger

from dashboard.cron_loop import stop as _stop_helper

BACKUP_DIR = Path(__file__).parent / "data" / "backups"
DB_PATH = Path(__file__).parent / "data" / "chat.db"
_RETENTION_DAYS = 7
_INTERVAL_HOURS = 6
_task: asyncio.Task | None = None


def _get_db_path() -> Path:
    return DB_PATH


def _get_backup_dir() -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    return BACKUP_DIR


def run_backup() -> Path | None:
    db = _get_db_path()
    if not db.exists():
        logger.warning("No DB to back up at {}", db)
        return None
    backup_dir = _get_backup_dir()
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"chat.db.{timestamp}.backup"
    try:
        con = sqlite3.connect(str(db))
        bck = sqlite3.connect(str(backup_path))
        con.backup(bck)
        bck.close()
        con.close()
        # verify
        vfy = sqlite3.connect(str(backup_path))
        cursor = vfy.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]
        vfy.close()
        if result != "ok":
            backup_path.unlink()
            logger.error("Backup integrity check failed: {}", result)
            return None
        logger.info("Backup created: {} ({} bytes)", backup_path, backup_path.stat().st_size)
        _prune_old(backup_dir)
        return backup_path
    except Exception as e:
        logger.error("Backup failed: {}", e)
        if backup_path.exists():
            backup_path.unlink()
        return None


def _prune_old(backup_dir: Path):
    cutoff = datetime.now(UTC).timestamp() - _RETENTION_DAYS * 86400
    for f in sorted(backup_dir.glob("chat.db.*.backup")):
        if f.stat().st_mtime < cutoff:
            f.unlink()
            logger.debug("Pruned old backup: {}", f)


def restore(backup_path: str) -> bool:
    db = _get_db_path()
    src = Path(backup_path)
    if not src.exists():
        logger.error("Backup file not found: {}", src)
        return False
    try:
        bck = sqlite3.connect(str(src))
        cursor = bck.execute("PRAGMA integrity_check")
        if cursor.fetchone()[0] != "ok":
            bck.close()
            logger.error("Backup file is corrupt")
            return False
        # close any active connections by renaming original and creating a new one
        if db.exists():
            db.rename(db.with_suffix(".db.prev"))
        dst = sqlite3.connect(str(db))
        bck.backup(dst)
        dst.close()
        bck.close()
        logger.info("Restored from {}", src)
        return True
    except Exception as e:
        logger.error("Restore failed: {}", e)
        return False


def last_backup_time() -> float | None:
    """Return the modification timestamp of the most recent backup, or None."""
    backup_dir = _get_backup_dir()
    backups = sorted(backup_dir.glob("chat.db.*.backup"), key=lambda f: f.stat().st_mtime, reverse=True)
    return backups[0].stat().st_mtime if backups else None


def start():
    global _task
    if _task is not None and not _task.done():
        return _task
    _task = asyncio.create_task(_loop())
    return _task


def stop():
    global _task
    _task = _stop_helper(_task)


async def _loop():
    while True:
        run_backup()
        await asyncio.sleep(_INTERVAL_HOURS * 3600)
