import asyncio
from datetime import UTC, datetime

from dashboard.orchestrator.agent_pool import pool
from dashboard.orchestrator.task_graph import TaskGraph, TaskStatus

# Graph ID -> asyncio.Queue for SSE events
_graph_queues: dict[str, asyncio.Queue] = {}

# Graph ID -> set of running subtask coroutines (for cancellation)
_running_tasks: dict[str, set[asyncio.Task]] = {}

# Graph ID -> cancellation flag
_cancelled: dict[str, bool] = {}


async def _emit_event(graph_id: str, event_type: str, data: dict):
    queue = _graph_queues.get(graph_id)
    if queue:
        await queue.put({"event": event_type, "data": data})


async def _run_subtask_command(graph_id: str, subtask, command: list[str], cwd: str | None) -> tuple[int, str]:
    await _emit_event(graph_id, "subtask_output", {
        "subtask_id": subtask.id,
        "line": f"Running: {' '.join(command)}",
    })
    try:
        proc = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=cwd,
        )
    except FileNotFoundError:
        return -1, f"Command not found: {command[0]}"

    output_lines = []
    while True:
        line_bytes = await proc.stdout.readline()
        if not line_bytes:
            break
        line = line_bytes.decode("utf-8", errors="replace").rstrip()
        output_lines.append(line)
        await _emit_event(graph_id, "subtask_output", {
            "subtask_id": subtask.id,
            "line": line,
        })

    await proc.wait()
    return proc.returncode or 0, "\n".join(output_lines)


async def _run_subtask(graph_id: str, subtask, semaphore: asyncio.Semaphore) -> str | None:
    if _cancelled.get(graph_id):
        subtask.status = TaskStatus.cancelled
        return None

    subtask.status = TaskStatus.running
    subtask.started_at = datetime.now(UTC)
    await _emit_event(graph_id, "subtask_started", {"subtask_id": subtask.id, "description": subtask.description})

    backend = pool.get_backend(subtask.agent_type)

    for attempt in range(subtask.max_retries + 1):
        if _cancelled.get(graph_id):
            subtask.status = TaskStatus.cancelled
            return None

        try:
            async with semaphore:
                if backend and hasattr(backend, "build_command"):
                    cmd = backend.build_command(subtask.description, session_id=None, input_files=[])
                else:
                    cmd = [subtask.agent_type, "-p", subtask.description]
                cmd = [c for c in cmd if c is not None]

                result = await asyncio.wait_for(
                    _run_subtask_command(graph_id, subtask, cmd, cwd=None),
                    timeout=subtask.timeout_seconds,
                )
                exit_code, output = result

                if _cancelled.get(graph_id):
                    subtask.status = TaskStatus.cancelled
                    return None

                if exit_code == 0:
                    subtask.status = TaskStatus.completed
                    subtask.result = output
                    subtask.completed_at = datetime.now(UTC)
                    await _emit_event(graph_id, "subtask_completed", {
                        "subtask_id": subtask.id,
                        "result": output[:1000],
                    })
                    return output
                else:
                    raise RuntimeError(f"Exit code {exit_code}: {output[:500]}")

        except TimeoutError:
            subtask.retry_count = attempt + 1
            if attempt < subtask.max_retries:
                subtask.status = TaskStatus.pending
                await _emit_event(graph_id, "subtask_retrying", {
                    "subtask_id": subtask.id,
                    "attempt": attempt + 1,
                    "error": "timeout",
                })
                continue
            subtask.status = TaskStatus.failed
            subtask.error = "timeout"
            subtask.completed_at = datetime.now(UTC)
            await _emit_event(graph_id, "subtask_failed", {
                "subtask_id": subtask.id,
                "error": "timeout",
                "attempts": attempt + 1,
            })
            return None

        except Exception as e:
            subtask.retry_count = attempt + 1
            if attempt < subtask.max_retries:
                subtask.status = TaskStatus.pending
                await _emit_event(graph_id, "subtask_retrying", {
                    "subtask_id": subtask.id,
                    "attempt": attempt + 1,
                    "error": str(e),
                })
                continue
            subtask.status = TaskStatus.failed
            subtask.error = str(e)
            subtask.completed_at = datetime.now(UTC)
            await _emit_event(graph_id, "subtask_failed", {
                "subtask_id": subtask.id,
                "error": str(e),
                "attempts": attempt + 1,
            })
            return None

    subtask.status = TaskStatus.failed
    subtask.completed_at = datetime.now(UTC)
    return None


async def execute_graph(graph: TaskGraph) -> TaskGraph:
    graph_id = graph.id
    _graph_queues[graph_id] = asyncio.Queue()
    _running_tasks[graph_id] = set()
    _cancelled[graph_id] = False

    semaphore = asyncio.Semaphore(5)
    graph.status = TaskStatus.running
    await _emit_event(graph_id, "task_started", {"task_id": graph_id, "root_task": graph.root_task})

    pending = set(graph.subtasks)

    while pending and not _cancelled.get(graph_id):
        ready = graph.ready_subtasks()
        ready = [st for st in ready if st in pending]
        if not ready:
            remaining = [st for st in pending if st.status == TaskStatus.pending]
            if not remaining:
                break
            await asyncio.sleep(0.5)
            continue

        tasks = []
        for st in ready:
            pending.discard(st)
            t = asyncio.create_task(_run_subtask(graph_id, st, semaphore))
            _running_tasks[graph_id].add(t)
            tasks.append(t)

        done, _ = await asyncio.wait(tasks)
        _running_tasks[graph_id] -= done

    if _cancelled.get(graph_id):
        graph.status = TaskStatus.cancelled
        graph.cancel_all()
    else:
        graph.status = TaskStatus.completed

    graph.completed_at = datetime.now(UTC)
    await _emit_event(graph_id, "task_completed", {
        "task_id": graph_id,
        "status": graph.status.value,
        "summary": graph.summary(),
    })

    return graph


async def cancel_graph(graph_id: str) -> bool:
    if graph_id not in _cancelled:
        return False
    _cancelled[graph_id] = True
    task_set = _running_tasks.get(graph_id, set())
    for t in task_set:
        t.cancel()
    task_set.clear()
    q = _graph_queues.get(graph_id)
    if q:
        await q.put({"event": "task_cancelled", "data": {"task_id": graph_id}})
    return True


def get_events_queue(graph_id: str) -> asyncio.Queue | None:
    return _graph_queues.get(graph_id)


def cleanup(graph_id: str):
    _graph_queues.pop(graph_id, None)
    _running_tasks.pop(graph_id, None)
    _cancelled.pop(graph_id, None)
