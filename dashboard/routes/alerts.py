from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from dashboard.alerts import alerts
from dashboard.rate_limit import limiter

router = APIRouter(prefix="/api", tags=["alerts"])


@router.get("/alerts")
@limiter.limit("30/minute")
async def list_alerts(request: Request, severity: str | None = None, component: str | None = None, limit: int = 50):
    return JSONResponse([
        {
            "id": a.id,
            "component": a.component,
            "severity": a.severity,
            "message": a.message,
            "details": a.details,
            "created_at": a.created_at.isoformat(),
            "acknowledged": a.acknowledged,
            "acknowledged_by": a.acknowledged_by,
        }
        for a in alerts.list(severity=severity, component=component, limit=limit)
    ])


@router.post("/alerts/{alert_id}/acknowledge")
@limiter.limit("30/minute")
async def acknowledge_alert(request: Request, alert_id: str):
    if alerts.acknowledge(alert_id):
        return JSONResponse({"status": "acknowledged"})
    return JSONResponse({"status": "not_found"}, status_code=404)


@router.post("/alerts/acknowledge-all")
@limiter.limit("10/minute")
async def acknowledge_all(request: Request, component: str | None = None):
    count = alerts.acknowledge_all(component=component)
    return JSONResponse({"status": "acknowledged", "count": count})
