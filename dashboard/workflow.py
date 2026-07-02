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

    steps = []
    for i, s in enumerate(data.get("steps", [])):
        steps.append(WorkflowStep(
            id=s.get("id", f"step-{i}"),
            description=s.get("description", ""),
            agent=s.get("agent", "developer"),
            depends_on=s.get("depends_on", []),
            approval_gate=s.get("approval_gate", False),
        ))

    return WorkflowDef(
        name=data.get("name", "untitled"),
        description=data.get("description", ""),
        steps=steps,
    )


# ── Engine ──────────────────────────────────────────────────────────────


class WorkflowEngine:
    def __init__(self, workflow: WorkflowDef, session_id: str):
        self.workflow = workflow
        self.session_id = session_id
        self.step_map: dict[str, WorkflowStep] = {s.id: s for s in workflow.steps}

    def ready_steps(self) -> list[WorkflowStep]:
        deps_met = []
        for step in self.workflow.steps:
            if step.status != "pending":
                continue
            if all(
                self.step_map.get(dep, WorkflowStep(id=dep, status="done")).status == "done"
                for dep in step.depends_on
            ):
                deps_met.append(step)
        return deps_met

    def all_done(self) -> bool:
        return all(s.status == "done" for s in self.workflow.steps)

    def summary(self) -> dict[str, Any]:
        by_status: dict[str, int] = {}
        for s in self.workflow.steps:
            by_status[s.status] = by_status.get(s.status, 0) + 1
        return {
            "workflow": self.workflow.name,
            "total_steps": len(self.workflow.steps),
            "by_status": by_status,
            "done": self.all_done(),
        }
