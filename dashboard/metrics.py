from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from prometheus_client import REGISTRY, Gauge, generate_latest

router = APIRouter(tags=["metrics"])

# Custom app metrics
_health = Gauge("health_check", "Health check result (1=healthy, 0=degraded, -1=unavailable)", ["component"])


@router.get("/metrics")
async def metrics():
    """Prometheus exposition format with live app metrics."""
    try:
        from dashboard.health import registry as hr
        results = await hr.run_all()
        _health.clear()
        for c in results:
            val = 1 if c.status == "healthy" else (0 if c.status == "degraded" else -1)
            _health.labels(component=c.name).set(val)
    except Exception:
        pass
    return PlainTextResponse(generate_latest(REGISTRY), media_type="text/plain; charset=utf-8")
