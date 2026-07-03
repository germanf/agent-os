import os
import sys
import time

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from dashboard.alerts import alerts
from dashboard.config import FRONTEND_DIST
from dashboard.config import VAULT_DIR as CONFIG_VAULT_DIR
from dashboard.health import HealthComponent, registry
from dashboard.hermes_adapter import get_version
from dashboard.kanban import is_available as kanban_available
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


def register_health_checks():
    registry.register("database", _check_db)
    registry.register("hermes", _check_hermes)
    registry.register("frontend", _check_frontend)
    registry.register("disk", _check_disk)
