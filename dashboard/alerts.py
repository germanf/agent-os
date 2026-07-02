import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from loguru import logger


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
        self._alerts: list[Alert] = []
        self._max_alerts = max_alerts

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
        if len(self._alerts) > self._max_alerts:
            self._alerts.pop(0)
        return alert

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


alerts = AlertManager()
