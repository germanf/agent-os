from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentContext:
    project_root: str
    session_id: str
    system_prompt: str | None = None
    env: dict[str, str] = field(default_factory=dict)


@dataclass
class AgentResult:
    success: bool
    summary: str
    details: dict[str, Any] = field(default_factory=dict)


class AgentCapability(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        ...

    def capability_id(self) -> str:
        return f"{type(self).__module__}.{type(self).__qualname__}"


class DeveloperCapability(AgentCapability):
    @property
    def name(self) -> str:
        return "developer"

    @property
    def description(self) -> str:
        return "Write, modify, and refactor source code"

    @abstractmethod
    async def fix_bug(self, description: str, context: AgentContext) -> AgentResult:
        ...

    @abstractmethod
    async def implement_feature(self, spec: str, context: AgentContext) -> AgentResult:
        ...

    @abstractmethod
    async def refactor(self, target: str, description: str, context: AgentContext) -> AgentResult:
        ...


class ReviewerCapability(AgentCapability):
    @property
    def name(self) -> str:
        return "reviewer"

    @property
    def description(self) -> str:
        return "Review code for quality, standards, and security"

    @abstractmethod
    async def review_pr(self, pr_details: dict, context: AgentContext) -> AgentResult:
        ...

    @abstractmethod
    async def check_standards(self, path: str, context: AgentContext) -> AgentResult:
        ...


class QACapability(AgentCapability):
    @property
    def name(self) -> str:
        return "qa"

    @property
    def description(self) -> str:
        return "Write and run tests, validate behavior"

    @abstractmethod
    async def write_tests(self, target: str, context: AgentContext) -> AgentResult:
        ...

    @abstractmethod
    async def run_validation(self, checks: list[str], context: AgentContext) -> AgentResult:
        ...
