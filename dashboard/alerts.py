import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime

import httpx
from loguru import logger

from dashboard.config import ALERT_WEBHOOK_URL


@dataclass
class Alert:
    id: str
    component: str
    severity: str  # critical | warning | info
    message: str
    details: dict | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    acknowledged: bool = False
    acknowledged_by: str | None = None


class AlertManager:
    def __init__(self, max_alerts: int = 1000):
        self._alerts: deque[Alert] = deque(maxlen=max_alerts)
        self._suppressed: dict[str, float] = {}  # component -> last alert time for rate limiting

    def emit(self, component: str, severity: str, message: str, details: dict | None = None) -> Alert:
        alert = Alert(
            id=str(uuid.uuid4()),
            component=component,
            severity=severity,
            message=message,
            details=details,
        )
        self._alerts.append(alert)
        log_fn = logger.critical if severity == "critical" else logger.warning if severity == "warning" else logger.info
        log_fn("[{}] {}: {} — {}", severity.upper(), component, message, details or "")
        if ALERT_WEBHOOK_URL:
            try:
                import asyncio
                asyncio.create_task(self._dispatch_webhook(alert))
            except RuntimeError:
                pass  # no event loop in this thread
        return alert

    async def _dispatch_webhook(self, alert: Alert) -> None:
        if not ALERT_WEBHOOK_URL:
            return
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(ALERT_WEBHOOK_URL, json={
                    "event": "alert",
                    "id": alert.id,
                    "component": alert.component,
                    "severity": alert.severity,
                    "message": alert.message,
                    "details": alert.details,
                    "created_at": alert.created_at.isoformat(),
                })
            logger.debug("Webhook dispatched for alert {}", alert.id)
        except Exception as e:
            logger.warning("Webhook dispatch failed: {}", e)

    def list(self, severity: str | None = None, component: str | None = None, limit: int = 50) -> list[Alert]:
        result = list(self._alerts)
        if severity:
            result = [a for a in result if a.severity == severity]
        if component:
            result = [a for a in result if a.component == component]
        return result[-limit:]

    def acknowledge(self, alert_id: str, by: str = "system") -> bool:
        for alert in self._alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                alert.acknowledged_by = by
                return True
        return False

    def acknowledge_all(self, component: str | None = None, by: str = "system") -> int:
        count = 0
        for alert in self._alerts:
            if not alert.acknowledged and (component is None or alert.component == component):
                alert.acknowledged = True
                alert.acknowledged_by = by
                count += 1
        return count

    def rate_limited(self, component: str, interval: float = 300.0) -> bool:
        """Return True if an alert for this component was emitted within `interval` seconds."""
        import time
        now = time.time()
        last = self._suppressed.get(component)
        if last is not None and now - last < interval:
            return True
        self._suppressed[component] = now
        return False


alerts = AlertManager()
