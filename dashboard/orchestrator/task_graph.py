import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class TaskStatus(StrEnum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


@dataclass
class SubTask:
    id: str
    description: str
    agent_type: str
    depends_on: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.pending
    timeout_seconds: int = 300
    retry_count: int = 0
    max_retries: int = 3
    result: str | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class TaskGraph:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    root_task: str = ""
    status: TaskStatus = TaskStatus.pending
    subtasks: list[SubTask] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None

    def add_subtask(self, description: str, agent_type: str,
                     depends_on: list[str] | None = None, timeout: int = 300) -> SubTask:
        st = SubTask(
            id=uuid.uuid4().hex[:8],
            description=description,
            agent_type=agent_type,
            depends_on=depends_on or [],
            timeout_seconds=timeout,
        )
        self.subtasks.append(st)
        return st

    def get_subtask(self, subtask_id: str) -> SubTask | None:
        for st in self.subtasks:
            if st.id == subtask_id:
                return st
        return None

    def ready_subtasks(self) -> list[SubTask]:
        return [
            st for st in self.subtasks
            if st.status == TaskStatus.pending
            and all(
                self.get_subtask(dep) and self.get_subtask(dep).status == TaskStatus.completed
                for dep in st.depends_on
            )
        ]

    def all_done(self) -> bool:
        return all(st.status in (TaskStatus.completed, TaskStatus.failed, TaskStatus.cancelled) for st in self.subtasks)

    def cancel_all(self):
        for st in self.subtasks:
            if st.status == TaskStatus.pending:
                st.status = TaskStatus.cancelled

    def summary(self) -> dict:
        counts = {}
        for st in self.subtasks:
            counts[st.status.value] = counts.get(st.status.value, 0) + 1
        return counts

    @classmethod
    def create_map_reduce(cls, root_task: str, map_description: str, parallelism: int,
                           reduce_description: str | None = None) -> "TaskGraph":
        lines = [ln.strip() for ln in root_task.split("\n") if ln.strip()]
        if not lines:
            lines = [root_task]

        graph = cls(root_task=root_task)

        chunks: list[list[str]] = [[] for _ in range(parallelism)]
        for i, line in enumerate(lines):
            chunks[i % parallelism].append(line)

        map_ids: list[str] = []
        for i, chunk in enumerate(chunks):
            if not chunk:
                continue
            desc = f"{map_description}\n\nInput chunk {i+1}/{len(chunks)}:\n" + "\n".join(chunk)
            st = graph.add_subtask(description=desc, agent_type="claude")
            map_ids.append(st.id)

        if not map_ids:
            return graph

        if reduce_description:
            reduce_desc = f"{reduce_description}\n\nSynthesize results from {len(map_ids)} parallel workers."
            graph.add_subtask(description=reduce_desc, agent_type="claude", depends_on=map_ids)

        return graph
