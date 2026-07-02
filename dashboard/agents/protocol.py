from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

# ── Handoff Protocol ──────────────────────────────────────────────────


class Severity(StrEnum):
    info = "info"
    warning = "warning"
    blocker = "blocker"
    critical = "critical"


class HandoffStatus(StrEnum):
    accepted = "accepted"
    rejected = "rejected"
    redirected = "redirected"


@dataclass
class HandoffRequest:
    from_role: str
    to_role: str
    session_id: str
    reason: str
    attempt_count: int = 0
    context_snapshot: str = ""
    severity: Severity = Severity.info
    issue_id: int | None = None


@dataclass
class HandoffResponse:
    from_role: str
    to_role: str
    session_id: str
    request_id: str
    status: HandoffStatus = HandoffStatus.accepted
    notes: str = ""


ALLOWED_ROLES = frozenset({
    "cto",
    "tech-lead",
    "fullstack-developer",
    "qa-tester",
    "security-specialist",
    "ui-ux-specialist",
    "advisory",
})


def validate_handoff(req: HandoffRequest) -> str | None:
    if req.from_role not in ALLOWED_ROLES:
        return f"Unknown from_role: {req.from_role}"
    if req.to_role not in ALLOWED_ROLES:
        return f"Unknown to_role: {req.to_role}"
    if not req.reason:
        return "reason is required"
    return None


# ── Core Protocol ─────────────────────────────────────────────────────


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
        for cls in type(self).__mro__:
            if cls is not type(self) and issubclass(cls, AgentCapability) and cls is not AgentCapability:
                return f"{cls.__module__}.{cls.__qualname__}"
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


class OrchestratorCapability(AgentCapability):
    """Decompose high-level goals into tasks, delegate, and track execution."""

    @property
    def name(self) -> str:
        return "orchestrator"

    @property
    def description(self) -> str:
        return "Task decomposition, delegation, and workflow execution"

    @abstractmethod
    async def decompose(
        self, goal: str, context: AgentContext
    ) -> AgentResult:
        """Break a high-level goal into a list of executable tasks."""

    @abstractmethod
    async def delegate(
        self, task_id: str, agent_name: str, context: AgentContext
    ) -> AgentResult:
        """Assign a kanban task to a named agent for execution."""

    @abstractmethod
    async def status(self, workflow_id: str) -> AgentResult:
        """Return the current status of all tasks in a workflow."""


class SecurityCapability(AgentCapability):
    """Pentesting, black-box testing, SAST/DAST, vulnerability auditing."""

    @property
    def name(self) -> str:
        return "security-specialist"

    @property
    def description(self) -> str:
        return "Penetration testing, security audit, dependency scanning"

    @abstractmethod
    async def run_static_analysis(self, path: str, context: AgentContext) -> AgentResult:
        ...

    @abstractmethod
    async def run_dependency_audit(self, context: AgentContext) -> AgentResult:
        ...

    @abstractmethod
    async def create_finding_issue(self, vuln: dict, context: AgentContext) -> AgentResult:
        ...


class UIUXCapability(AgentCapability):
    """Design system review, accessibility audit, responsive checks."""

    @property
    def name(self) -> str:
        return "ui-ux-specialist"

    @property
    def description(self) -> str:
        return "Design review, accessibility audit, UI consistency"

    @abstractmethod
    async def review_design(self, path: str, context: AgentContext) -> AgentResult:
        ...

    @abstractmethod
    async def audit_accessibility(self, path: str, context: AgentContext) -> AgentResult:
        ...

    @abstractmethod
    async def create_design_issue(self, finding: dict, context: AgentContext) -> AgentResult:
        ...
