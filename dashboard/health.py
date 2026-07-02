from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from loguru import logger


@dataclass
class HealthComponent:
    name: str
    status: str  # healthy | degraded | unavailable
    latency_ms: float
    details: dict | None = None
    last_success: datetime | None = None
    last_failure: datetime | None = None


class HealthRegistry:
    def __init__(self):
        self._checks: dict[str, Callable[[], HealthComponent]] = {}

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


registry = HealthRegistry()
