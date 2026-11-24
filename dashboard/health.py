import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from loguru import logger

from dashboard.config import ALERT_HEALTH_DEGRADED_INTERVAL


@dataclass
class HealthComponent:
    name: str
    status: str  # healthy | degraded | unavailable
    latency_ms: float
    details: dict | None = None
    last_success: datetime | None = None
    last_failure: datetime | None = None


@dataclass
class HealthSnapshot:
    timestamp: float
    overall: str
    components: list[dict]


class HealthRegistry:
    def __init__(self):
        self._checks: dict[str, Callable[[], HealthComponent]] = {}
        self._history: deque[HealthSnapshot] = deque(maxlen=200)

    def register(self, name: str, check: Callable[[], HealthComponent]) -> None:
        self._checks[name] = check
        logger.debug("Registered health check: {}", name)

    async def run_all(self) -> list[HealthComponent]:
        results = []
        for name, check in self._checks.items():
            try:
                result = check()
                results.append(result)
            except Exception as e:
                results.append(HealthComponent(
                    name=name,
                    status="unavailable",
                    latency_ms=0,
                    details={"error": str(e)},
                ))
        overall = "healthy"
        for c in results:
            if c.status == "unavailable":
                overall = "unavailable"
            elif c.status == "degraded" and overall == "healthy":
                overall = "degraded"
        self._history.append(HealthSnapshot(
            timestamp=time.time(),
            overall=overall,
            components=[c.__dict__ for c in results],
        ))
        # Auto-alert on degraded/unavailable (rate-limited per component)
        try:
            from dashboard.alerts import alerts
            for c in results:
                if c.status in ("degraded", "unavailable"):
                    if not alerts.rate_limited(c.name, ALERT_HEALTH_DEGRADED_INTERVAL):
                        alerts.emit(
                            component=f"health.{c.name}",
                            severity="warning" if c.status == "degraded" else "critical",
                            message=f"Health check {c.name} is {c.status}",
                            details=c.details,
                        )
        except Exception:
            pass  # alert emission failures should not break health checks
        return results

    async def run(self, name: str) -> HealthComponent | None:
        check = self._checks.get(name)
        if not check:
            return None
        try:
            return check()
        except Exception as e:
            return HealthComponent(
                name=name,
                status="unavailable",
                latency_ms=0,
                details={"error": str(e)},
            )

    def list_checks(self) -> list[str]:
        return list(self._checks.keys())

    def history(self, limit: int = 100) -> list[dict]:
        return [s.__dict__ for s in list(self._history)[-limit:]]


registry = HealthRegistry()
