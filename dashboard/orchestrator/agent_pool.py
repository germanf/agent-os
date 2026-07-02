import time
from dataclasses import dataclass

from loguru import logger

from dashboard.backends import get as get_backend
from dashboard.backends import list_all_registered
from dashboard.backends.protocol import ChatBackend


@dataclass
class AgentProfile:
    agent_type: str
    capabilities: list[str]
    estimated_cost_per_token: float = 0.0
    max_concurrency: int = 1
    available: bool = True
    health_status: str = "healthy"
    health_last_check: float = 0.0


class AgentPool:
    def __init__(self):
        self._agents: dict[str, AgentProfile] = {}
        self._backends: dict[str, ChatBackend] = {}
        self._refresh()

    def _refresh(self):
        for name in list_all_registered():
            if name not in self._agents:
                backend = get_backend(name)
                available = backend is not None and backend.validate_available()
                self._agents[name] = AgentProfile(
                    agent_type=name,
                    capabilities=["coding", "chat"],
                    available=available,
                    health_status="healthy" if available else "unavailable",
                )
                if backend:
                    self._backends[name] = backend

    def register(self, backend: ChatBackend):
        name = backend.name
        available = backend.validate_available()
        self._agents[name] = AgentProfile(
            agent_type=name,
            capabilities=["coding", "chat"],
            available=available,
        )
        self._backends[name] = backend
        logger.info("Registered agent: {} (available: {})", name, available)

    def deregister(self, agent_type: str):
        self._agents.pop(agent_type, None)
        self._backends.pop(agent_type, None)
        logger.info("Deregistered agent: {}", agent_type)

    def get_backend(self, agent_type: str) -> ChatBackend | None:
        self._refresh()
        return self._backends.get(agent_type)

    def list_profiles(self) -> list[AgentProfile]:
        self._refresh()
        now = time.time()
        for p in self._agents.values():
            if now - p.health_last_check > 60:
                backend = self._backends.get(p.agent_type)
                if backend:
                    p.available = backend.validate_available()
                    p.health_status = "healthy" if p.available else "unavailable"
                p.health_last_check = now
        return list(self._agents.values())

    def get_available(self) -> list[AgentProfile]:
        return [p for p in self.list_profiles() if p.available]


pool = AgentPool()
