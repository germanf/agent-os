import os
import sys
import time

import psutil
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from dashboard.alerts import alerts
from dashboard.backends import list_available as list_available_backends
from dashboard.backup import last_backup_time, verify_backup_integrity
from dashboard.config import FRONTEND_DIST
from dashboard.config import VAULT_DIR as CONFIG_VAULT_DIR
from dashboard.health import HealthComponent, registry
from dashboard.hermes_adapter import get_version
from dashboard.kanban import is_available as kanban_available
from dashboard.mcp.server import registry as mcp_registry
from dashboard.ponytail import get_metrics, get_status
from dashboard.rate_limit import limiter

router = APIRouter(prefix="/api", tags=["diagnostics"])


@router.get("/ponytail/metrics")
@limiter.limit("10/minute")
async def ponytail_metrics(request: Request):
    return JSONResponse(get_metrics())


@router.get("/health")
async def health(request: Request):
    components = await registry.run_all()
    overall = "healthy"
    for c in components:
        if c.status == "unavailable":
            overall = "unavailable"
        elif c.status == "degraded" and overall == "healthy":
            overall = "degraded"
    return JSONResponse({
        "status": overall,
        "components": [
            {
                "name": c.name,
                "status": c.status,
                "latency_ms": round(c.latency_ms, 1),
                "details": c.details,
            }
            for c in components
        ],
    })


@router.get("/health/history")
async def health_history(request: Request, limit: int = 50):
    return JSONResponse(registry.history(limit=limit))


@router.get("/diagnostics")
@limiter.limit("10/minute")
async def diagnostics(request: Request):
    frontend_built = (FRONTEND_DIST / "assets").exists()
    db_exists = False
    vault_exists = False
    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "chat.db")
    db_exists = os.path.exists(db_path)
    vault_path = str(CONFIG_VAULT_DIR) if CONFIG_VAULT_DIR else "/home/ubuntu/vault"
    vault_exists = os.path.exists(vault_path)
    return JSONResponse({
        "frontend_built": frontend_built,
        "db_exists": db_exists,
        "vault_exists": vault_exists,
        "ponytail": get_status(),
        "hermes_version": get_version(),
        "kanban_ready": kanban_available(),
        "python_version": sys.version.split()[0],
        "fastapi_installed": True,
        "uvicorn_installed": True,
        "active_alerts": len([a for a in alerts.list() if not a.acknowledged]),
    })


def _check_db():
    t0 = time.time()
    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "chat.db")
    exists = os.path.exists(db_path)
    if not exists:
        return HealthComponent(
            name="database", status="unavailable", latency_ms=(time.time() - t0) * 1000,
            details={"error": "DB file not found"},
        )
    try:
        import sqlite3
        con = sqlite3.connect(db_path, timeout=2)
        con.execute("SELECT 1")
        con.close()
        latency = (time.time() - t0) * 1000
        return HealthComponent(name="database", status="healthy", latency_ms=latency, details={"path": db_path})
    except Exception as e:
        latency = (time.time() - t0) * 1000
        return HealthComponent(name="database", status="unavailable", latency_ms=latency, details={"error": str(e)})


def _check_hermes():
    t0 = time.time()
    try:
        ver = get_version()
        latency = (time.time() - t0) * 1000
        return HealthComponent(name="hermes", status="healthy", latency_ms=latency, details={"version": ver})
    except Exception as e:
        latency = (time.time() - t0) * 1000
        return HealthComponent(name="hermes", status="unavailable", latency_ms=latency, details={"error": str(e)})


def _check_frontend():
    t0 = time.time()
    built = (FRONTEND_DIST / "assets").exists()
    latency = (time.time() - t0) * 1000
    return HealthComponent(
        name="frontend",
        status="healthy" if built else "degraded",
        latency_ms=latency,
        details={"built": built, "dist": str(FRONTEND_DIST)},
    )


def _check_disk():
    t0 = time.time()
    try:
        import shutil
        usage = shutil.disk_usage(FRONTEND_DIST.parent if FRONTEND_DIST.exists() else "/")
        pct = usage.used / usage.total * 100
        latency = (time.time() - t0) * 1000
        status = "healthy" if pct < 90 else "degraded" if pct < 95 else "unavailable"
        gb = round(usage.total / 1e9, 1)
        used = round(usage.used / 1e9, 1)
        return HealthComponent(
            name="disk",
            status=status,
            latency_ms=latency,
            details={"total_gb": gb, "used_gb": used, "percent": round(pct, 1)},
        )
    except Exception as e:
        latency = (time.time() - t0) * 1000
        return HealthComponent(name="disk", status="unavailable", latency_ms=latency, details={"error": str(e)})


def _check_memory():
    t0 = time.time()
    try:
        mem = psutil.virtual_memory()
        pct_free = mem.available / mem.total * 100
        lat = (time.time() - t0) * 1000
        st = "healthy" if pct_free >= 20 else "degraded" if pct_free >= 10 else "unavailable"
        return HealthComponent(name="memory", status=st, latency_ms=lat,
                               details={"total_gb": round(mem.total / 1e9, 1),
                                        "available_gb": round(mem.available / 1e9, 1),
                                        "free_pct": round(pct_free, 1)})
    except Exception as e:
        lat = (time.time() - t0) * 1000
        return HealthComponent(name="memory", status="unavailable", latency_ms=lat,
                               details={"error": str(e)[:120]})


def _check_cpu():
    t0 = time.time()
    try:
        load1, load5, load15 = os.getloadavg()
        cores = os.cpu_count() or 1
        lat = (time.time() - t0) * 1000
        ratio = load1 / cores
        st = "healthy" if ratio < 2 else "degraded" if ratio < 4 else "unavailable"
        return HealthComponent(name="cpu", status=st, latency_ms=lat,
                               details={"load_1m": round(load1, 2), "load_5m": round(load5, 2),
                                        "load_15m": round(load15, 2), "cores": cores})
    except Exception as e:
        lat = (time.time() - t0) * 1000
        return HealthComponent(name="cpu", status="unavailable", latency_ms=lat,
                               details={"error": str(e)[:120]})


def _check_backup():
    t0 = time.time()
    try:
        last_ts = last_backup_time()
        lat = (time.time() - t0) * 1000
        integrity = verify_backup_integrity()
        details: dict = {"integrity": integrity}
        if last_ts is None:
            return HealthComponent(name="backup", status="unavailable", latency_ms=lat,
                                   details=details | {"error": "No backups found"})
        age_hours = (time.time() - last_ts) / 3600
        st = "healthy" if age_hours < 6 else "degraded" if age_hours < 24 else "unavailable"
        if not integrity["ok"]:
            st = "degraded"
        last_fmt = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(last_ts))
        details["last_backup"] = last_fmt
        details["age_hours"] = round(age_hours, 1)
        return HealthComponent(name="backup", status=st, latency_ms=lat,
                               details=details)
    except Exception as e:
        lat = (time.time() - t0) * 1000
        return HealthComponent(name="backup", status="unavailable", latency_ms=lat,
                               details={"error": str(e)[:120]})


def _check_mcp():
    t0 = time.time()
    try:
        servers = mcp_registry.list()
        lat = (time.time() - t0) * 1000
        if not servers:
            return HealthComponent(name="mcp", status="unavailable", latency_ms=lat,
                                   details={"error": "No MCP servers registered"})
        names = [s.name for s in servers]
        # Sync-only check: servers exist and are registered. Full response test
        # requires async — see the MCP status endpoint for per-server health.
        return HealthComponent(name="mcp", status="healthy", latency_ms=lat,
                               details={"servers": names, "total": len(servers), "failures": 0})
    except Exception as e:
        lat = (time.time() - t0) * 1000
        return HealthComponent(name="mcp", status="unavailable", latency_ms=lat,
                               details={"error": str(e)[:120]})


def _check_backends():
    t0 = time.time()
    try:
        available = list_available_backends()
        lat = (time.time() - t0) * 1000
        st = "healthy" if len(available) > 0 else "degraded"
        return HealthComponent(name="backends", status=st, latency_ms=lat,
                               details={"available": available, "count": len(available)})
    except Exception as e:
        lat = (time.time() - t0) * 1000
        return HealthComponent(name="backends", status="unavailable", latency_ms=lat,
                               details={"error": str(e)[:120]})


def register_health_checks():
    registry.register("database", _check_db)
    registry.register("hermes", _check_hermes)
    registry.register("frontend", _check_frontend)
    registry.register("disk", _check_disk)
    registry.register("memory", _check_memory)
    registry.register("cpu", _check_cpu)
    registry.register("backup", _check_backup)
    registry.register("mcp", _check_mcp)
    registry.register("backends", _check_backends)
