from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from dashboard.alerts import alerts
from dashboard.rate_limit import limiter

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("")
@limiter.limit("30/minute")
async def list_alerts(
    request: Request,
    severity: str | None = None,
    component: str | None = None,
    limit: int = 50,
):
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


@router.post("/{alert_id}/acknowledge")
@limiter.limit("30/minute")
async def acknowledge_alert(request: Request, alert_id: str, body: dict | None = None):
    by = (body or {}).get("by", "ui")
    ok = alerts.acknowledge(alert_id, by=by)
    if not ok:
        return JSONResponse({"error": "Alert not found"}, status_code=404)
    return JSONResponse({"status": "acknowledged"})


@router.post("/acknowledge-all")
@limiter.limit("10/minute")
async def acknowledge_all(request: Request, body: dict | None = None):
    component = (body or {}).get("component")
    by = (body or {}).get("by", "ui")
    count = alerts.acknowledge_all(component=component, by=by)
    return JSONResponse({"acknowledged": count})
