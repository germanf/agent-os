from __future__ import annotations

from dashboard import kanban
from dashboard.agents.protocol import (
    AgentContext,
    AgentResult,
    OrchestratorCapability,
)
from dashboard.headroom_memory import HeadroomSessionMemory
from dashboard.hermes_adapter import is_available


class HermesAgent(OrchestratorCapability):
    def __init__(self) -> None:
        self._memory = HeadroomSessionMemory()

    @property
    def description(self) -> str:
        return "Hermes-powered orchestrator — decompose, delegate, track"

    async def decompose(self, goal: str, context: AgentContext) -> AgentResult:
        if not is_available():
            return AgentResult(success=False, summary="Hermes CLI not available")

        tasks = [t.strip() for t in goal.split("\n") if t.strip()]
        created = []
        for task in tasks:
            t = await kanban.create_task(
                title=task[:200],
                tenant=context.session_id,
            )
            if t:
                created.append(t)

        return AgentResult(
            success=len(created) > 0,
            summary=f"Decomposed into {len(tasks)} tasks, created {len(created)} kanban cards",
            details={"tasks": tasks, "kanban_cards": created},
        )

    async def delegate(self, task_id: str, agent_name: str, context: AgentContext) -> AgentResult:
        if not is_available():
            return AgentResult(success=False, summary="Hermes CLI not available")
        comment = f"Assigned to {agent_name}"
        ok = await kanban.comment_task(task_id, comment)
        return AgentResult(
            success=ok,
            summary=f"{'Delegated' if ok else 'Failed to delegate'} task {task_id} to {agent_name}",
            details={"task_id": task_id, "agent": agent_name},
        )

    async def status(self, workflow_id: str) -> AgentResult:
        if not is_available():
            return AgentResult(success=False, summary="Hermes CLI not available")
        tasks = await kanban.list_tasks(tenant=workflow_id)
        by_status: dict[str, list[dict]] = {}
        for t in tasks:
            s = t.get("status", "unknown")
            by_status.setdefault(s, []).append(t)
        return AgentResult(
            success=True,
            summary=f"Workflow {workflow_id}: {len(tasks)} tasks ({len(by_status.get('done', []))} done)",
            details={"workflow_id": workflow_id, "tasks_by_status": by_status, "total": len(tasks)},
        )
