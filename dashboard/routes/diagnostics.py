import os
import sys

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from dashboard.config import FRONTEND_DIST
from dashboard.hermes_adapter import get_version as hermes_version
from dashboard.ponytail import get_metrics, get_status
from dashboard.rate_limit import limiter

router = APIRouter(prefix="/api", tags=["diagnostics"])


@router.get("/ponytail/metrics")
@limiter.limit("10/minute")
async def ponytail_metrics(request: Request):
    return JSONResponse(get_metrics())


@router.get("/health")
async def health(request: Request):
    return {"status": "ok"}


@router.get("/diagnostics")
@limiter.limit("10/minute")
async def diagnostics(request: Request):
    frontend_built = (FRONTEND_DIST / "assets").exists()
    db_exists = False
    vault_exists = False
    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "chat.db")
    db_exists = os.path.exists(db_path)
    try:
        vault_path = os.environ.get("VAULT_DIR", "/home/ubuntu/vault")
        vault_exists = os.path.exists(vault_path)
    except Exception:
        pass
    return JSONResponse({
        "frontend_built": frontend_built,
        "db_exists": db_exists,
        "vault_exists": vault_exists,
        "ponytail": get_status(),
        "hermes_version": hermes_version(),
        "python_version": sys.version.split()[0],
        "fastapi_installed": True,
        "uvicorn_installed": True,
    })
