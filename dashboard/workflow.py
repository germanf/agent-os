from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # ponytail: yaml optional, json-only fallback


# ── Data Model ──────────────────────────────────────────────────────────


@dataclass
class WorkflowStep:
    id: str
    description: str = ""
    agent: str = "developer"
    depends_on: list[str] = field(default_factory=list)
    approval_gate: bool = False
    status: str = "pending"
    result: dict[str, Any] | None = None
    retry_count: int = 0
    max_retries: int = 3
    error: str | None = None


@dataclass
class WorkflowDef:
    name: str
    description: str = ""
    steps: list[WorkflowStep] = field(default_factory=list)


# ── Parser ──────────────────────────────────────────────────────────────


def parse_workflow(source: str | dict[str, Any] | Path) -> WorkflowDef:
    if isinstance(source, Path):
        raw = source.read_text()
    elif isinstance(source, str):
        raw = source
    else:
        raw = json.dumps(source)

    data: dict[str, Any] | None = None
    parsed = False

    if yaml is not None and not parsed:
        try:
            data = yaml.safe_load(raw)
            if isinstance(data, dict):
                parsed = True
        except yaml.YAMLError:
            pass

    if not parsed:
        try:
            data = json.loads(raw)
            parsed = True
        except json.JSONDecodeError:
            pass

    if not parsed or data is None:
        raise ValueError("Workflow must be valid YAML or JSON")

    defaults = data.get("defaults", {})
    default_max_retries = defaults.get("max_retries", 3)

    steps = []
    for i, s in enumerate(data.get("steps", [])):
        loop_config = s.get("loop", {})
        steps.append(WorkflowStep(
            id=s.get("id", f"step-{i}"),
            description=s.get("description", ""),
            agent=s.get("agent", "developer"),
            depends_on=s.get("depends_on", []),
            approval_gate=s.get("approval_gate", False),
            max_retries=loop_config.get("max_retries", default_max_retries),
        ))

    return WorkflowDef(
        name=data.get("name", "untitled"),
        description=data.get("description", ""),
        steps=steps,
    )


# ── Engine (Active) ─────────────────────────────────────────────────────


class WorkflowEngine:
    def __init__(self, workflow: WorkflowDef, session_id: str):
        self.workflow = workflow
        self.session_id = session_id
        self.step_map: dict[str, WorkflowStep] = {s.id: s for s in workflow.steps}
        self._on_approval_gate: callable | None = None
        self._on_step_ready: callable | None = None
        self._on_escalate: callable | None = None

    def on_approval_gate(self, handler: callable) -> None:
        self._on_approval_gate = handler

    def on_step_ready(self, handler: callable) -> None:
        self._on_step_ready = handler

    def on_escalate(self, handler: callable) -> None:
        self._on_escalate = handler

    def ready_steps(self) -> list[WorkflowStep]:
        deps_met = []
        for step in self.workflow.steps:
            if step.status not in ("pending", "failed"):
                continue
            if all(
                self.step_map.get(dep, WorkflowStep(id=dep, status="done")).status == "done"
                for dep in step.depends_on
            ):
                deps_met.append(step)
        return deps_met

    def all_done(self) -> bool:
        return all(s.status == "done" for s in self.workflow.steps)

    def mark_step(self, step_id: str, status: str, error: str | None = None) -> None:
        step = self.step_map.get(step_id)
        if step:
            step.status = status
            step.error = error

    def mark_loop_iteration(self, step_id: str) -> str | None:
        step = self.step_map.get(step_id)
        if not step:
            return None
        step.retry_count += 1
        if step.retry_count >= step.max_retries:
            step.status = "escalated"
            if self._on_escalate:
                self._on_escalate(step)
            return "escalate"
        step.status = "pending"
        return "retry"

    async def execute_ready_steps(self):
        for step in self.ready_steps():
            if step.approval_gate:
                if self._on_approval_gate:
                    await self._on_approval_gate(step)
                continue  # wait for external approval
            if self._on_step_ready:
                await self._on_step_ready(step)

    def summary(self) -> dict[str, Any]:
        by_status: dict[str, int] = {}
        for s in self.workflow.steps:
            by_status[s.status] = by_status.get(s.status, 0) + 1
        return {
            "workflow": self.workflow.name,
            "total_steps": len(self.workflow.steps),
            "by_status": by_status,
            "done": self.all_done(),
            "session_id": self.session_id,
        }
