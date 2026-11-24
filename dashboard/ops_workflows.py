"""10 autonomous operational workflows for cron-driven maintenance."""
from __future__ import annotations

import shutil
import time
from collections.abc import Callable, Coroutine
from typing import Any

from loguru import logger

from dashboard.chat_store import DB_PATH, _connect

_WORKFLOW_REGISTRY: dict[str, dict[str, Any]] = {}


def register(
    name: str, interval_min: int = 30, enabled: bool = True
) -> Callable[[Callable[..., Coroutine]], Callable[..., Coroutine]]:
    def wrapper(func: Callable[..., Coroutine]) -> Callable[..., Coroutine]:
        _WORKFLOW_REGISTRY[name] = {
            "func": func,
            "interval_min": interval_min,
            "enabled": enabled,
            "last_tick": 0.0,
            "running": False,
        }
        return func
    return wrapper


def list_workflows() -> dict[str, dict[str, Any]]:
    return {k: {kk: vv for kk, vv in v.items() if kk != "func"} for k, v in _WORKFLOW_REGISTRY.items()}


@register("system_health")
async def system_health() -> dict[str, Any]:
    from dashboard.health import registry
    results = await registry.run_all()
    for hc in results:
        logger.info("Health [{}] status={}", hc.name, hc.status)
    return {"checks": len(results), "failures": sum(1 for h in results if h.status != "healthy")}


@register("db_backup")
async def db_backup() -> dict[str, Any]:
    backup_dir = DB_PATH.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    backup_path = backup_dir / f"chat.{ts}.db"
    if DB_PATH.exists():
        shutil.copy2(DB_PATH, backup_path)
        extant = sorted(backup_dir.glob("chat.*.db"), reverse=True)
        for old in extant[5:]:
            old.unlink()
        logger.info("DB backed up: {} ({} kept)", backup_path, min(len(extant), 5))
        return {"backup": str(backup_path), "kept": min(len(extant), 5)}
    return {"error": "chat.db not found"}


@register("job_evict")
async def job_evict() -> dict[str, Any]:
    from dashboard.runner import _FINISHED_STATUSES, _jobs
    now = time.time()
    before = len(_jobs)
    to_delete = []
    for jid, job in list(_jobs.items()):
        if job.status in _FINISHED_STATUSES:
            age = now - (job.ended_at or job.started_at)
            if age > 3600:
                to_delete.append(jid)
    for jid in to_delete:
        _jobs.pop(jid, None)
    logger.info("Evicted {} finished jobs ({} remaining)", len(to_delete), len(_jobs))
    return {"evicted": len(to_delete), "remaining": len(_jobs), "before": before}


@register("chat_prune")
async def chat_prune() -> dict[str, Any]:
    cutoff = time.time() - 7 * 86400
    pruned = 0
    async with _connect() as conn:
        cur = await conn.execute(
            "DELETE FROM messages WHERE created_at < ?", (cutoff,)
        )
        pruned = cur.rowcount
        logger.info("Pruned {} old messages", pruned)
    return {"pruned_messages": pruned}


@register("headroom_learn")
async def headroom_learn() -> dict[str, Any]:
    try:
        from dashboard.headroom_learn import compute_baseline
        baseline = await compute_baseline()
        logger.info("Headroom baseline: {}", baseline)
        return {"baseline": baseline}
    except Exception as e:
        logger.warning("Headroom learning skipped: {}", e)
        return {"skipped": str(e)}


@register("token_log")
async def token_log() -> dict[str, Any]:
    try:
        from dashboard.token_accounting import get_daily_usage
        usage = await get_daily_usage()
        logger.info("Token usage: {}", usage)
        return {"usage": usage}
    except Exception as e:
        logger.warning("Token log skipped: {}", e)
        return {"skipped": str(e)}


@register("diagnostics")
async def diagnostics() -> dict[str, Any]:
    info: dict[str, Any] = {
        "timestamp": time.time(),
        "db_exists": DB_PATH.exists(),
        "db_size": DB_PATH.stat().st_size if DB_PATH.exists() else 0,
    }
    async with _connect() as conn:
        for table in ("projects", "chats", "messages", "workflow_runs"):
            try:
                cur = await conn.execute(f"SELECT COUNT(*) as cnt FROM {table}")
                row = await cur.fetchone()
                info[f"{table}_count"] = row["cnt"] if row else 0
            except Exception:
                info[f"{table}_count"] = -1
    try:
        from dashboard.runner import _jobs
        info["active_jobs"] = sum(1 for j in _jobs.values() if j.status.value == "running")
        info["total_jobs"] = len(_jobs)
    except Exception:
        pass
    logger.info("Diagnostics: {}", info)
    return info


@register("alerts_prune")
async def alerts_prune() -> dict[str, Any]:
    from dashboard.alerts import alerts
    before = len(alerts._alerts)
    alerts._alerts = [a for a in alerts._alerts if a.get("severity") in ("critical", "warning")]
    pruned = before - len(alerts._alerts)
    logger.info("Pruned {} non-critical alerts ({} remain)", pruned, len(alerts._alerts))
    return {"pruned": pruned, "remaining": len(alerts._alerts)}


@register("workflow_log_cleanup")
async def workflow_log_cleanup() -> dict[str, Any]:
    cutoff = time.time() - 30 * 86400
    async with _connect() as conn:
        cur = await conn.execute(
            "DELETE FROM workflow_runs WHERE started_at < ?", (cutoff,)
        )
        pruned = cur.rowcount
        logger.info("Pruned {} old workflow run records", pruned)
    return {"pruned": pruned}


@register("scheduler_self_check")
async def scheduler_self_check() -> dict[str, Any]:
    """Log scheduler status: which workflows are running, stuck, or due."""
    now = time.time()
    statuses = {}
    for name, cfg in _WORKFLOW_REGISTRY.items():
        statuses[name] = {
            "enabled": cfg["enabled"],
            "running": cfg["running"],
            "interval_min": cfg["interval_min"],
            "seconds_since_tick": now - cfg["last_tick"],
        }
    logger.info("Scheduler self-check: {}", statuses)
    return statuses
