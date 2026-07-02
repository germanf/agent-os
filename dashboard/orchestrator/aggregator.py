from dashboard.orchestrator.task_graph import TaskGraph, TaskStatus


def aggregate_results(graph: TaskGraph) -> str:
    parts = []
    for st in graph.subtasks:
        header = f"## {st.description} ({st.agent_type})"
        if st.status == TaskStatus.completed and st.result:
            parts.append(f"{header}\n\n{st.result}")
        elif st.status == TaskStatus.failed:
            parts.append(f"{header}\n\n**Failed**: {st.error or 'Unknown error'}")
        elif st.status == TaskStatus.cancelled:
            parts.append(f"{header}\n\n_Cancelled_")
        else:
            parts.append(f"{header}\n\n_Pending or in progress_")
    return "\n\n---\n\n".join(parts)
