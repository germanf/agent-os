import asyncio
import json

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from dashboard.orchestrator.agent_pool import pool
from dashboard.orchestrator.executor import cancel_graph, cleanup, execute_graph, get_events_queue
from dashboard.orchestrator.task_graph import TaskGraph, TaskStatus
from dashboard.rate_limit import limiter

router = APIRouter(prefix="/api/orchestrator", tags=["orchestrator"])

# In-memory task store (ponytail: no DB needed for ephemeral execution state)
_graphs: dict[str, TaskGraph] = {}
_MAX_GRAPHS = 200


@router.post("/tasks")
@limiter.limit("10/minute")
async def create_task(request: Request, body: dict):
    root_task = body.get("root_task", "")
    subtasks_data = body.get("subtasks", [])

    graph = TaskGraph(root_task=root_task)

    if subtasks_data:
        for sd in subtasks_data:
            graph.add_subtask(
                description=sd.get("description", ""),
                agent_type=sd.get("agent_type", "claude"),
                depends_on=sd.get("depends_on", []),
                timeout=sd.get("timeout_seconds", 300),
            )
    elif root_task:
        lines = [ln.strip() for ln in root_task.split("\n") if ln.strip()]
        available = pool.get_available()
        if not available:
            available = pool.list_profiles()
        for i, line in enumerate(lines):
            agent = available[i % len(available)].agent_type if available else "claude"
            graph.add_subtask(description=line, agent_type=agent)

    _prune_old()
    _graphs[graph.id] = graph

    asyncio.create_task(execute_graph(graph))

    return JSONResponse({
        "task_id": graph.id,
        "status": graph.status.value,
        "subtasks": [
            {"id": st.id, "description": st.description, "agent_type": st.agent_type, "status": st.status.value}
            for st in graph.subtasks
        ],
    }, status_code=201)


@router.get("/tasks")
@limiter.limit("30/minute")
async def list_tasks(request: Request):
    return JSONResponse([
        {
            "id": g.id,
            "root_task": g.root_task[:100],
            "status": g.status.value,
            "subtask_count": len(g.subtasks),
            "created_at": g.created_at.isoformat(),
            "summary": g.summary(),
        }
        for g in _graphs.values()
    ])


@router.get("/tasks/{task_id}")
@limiter.limit("30/minute")
async def get_task(request: Request, task_id: str):
    graph = _graphs.get(task_id)
    if not graph:
        return JSONResponse({"error": "Task not found"}, status_code=404)
    return JSONResponse({
        "id": graph.id,
        "root_task": graph.root_task,
        "status": graph.status.value,
        "created_at": graph.created_at.isoformat(),
        "completed_at": graph.completed_at.isoformat() if graph.completed_at else None,
        "subtasks": [
            {
                "id": st.id,
                "description": st.description,
                "agent_type": st.agent_type,
                "depends_on": st.depends_on,
                "status": st.status.value,
                "timeout_seconds": st.timeout_seconds,
                "retry_count": st.retry_count,
                "max_retries": st.max_retries,
                "result": st.result[:2000] if st.result else None,
                "error": st.error,
                "started_at": st.started_at.isoformat() if st.started_at else None,
                "completed_at": st.completed_at.isoformat() if st.completed_at else None,
            }
            for st in graph.subtasks
        ],
        "summary": graph.summary(),
    })


@router.delete("/tasks/{task_id}")
@limiter.limit("10/minute")
async def cancel_task(request: Request, task_id: str):
    if task_id not in _graphs:
        return JSONResponse({"error": "Task not found"}, status_code=404)
    await cancel_graph(task_id)
    graph = _graphs[task_id]
    graph.status = TaskStatus.cancelled
    graph.cancel_all()
    return JSONResponse({"status": "cancelled"})


@router.get("/tasks/{task_id}/stream")
async def stream_task(request: Request, task_id: str):
    if task_id not in _graphs:
        return JSONResponse({"error": "Task not found"}, status_code=404)

    queue = get_events_queue(task_id)
    if queue is None:
        return JSONResponse({"error": "Task not started or already finished"}, status_code=400)

    async def event_stream():
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=25)
                except TimeoutError:
                    yield "event: ping\ndata: {}\n\n"
                    continue
                if event.get("event") == "task_completed" or event.get("event") == "task_cancelled":
                    yield f"event: {event['event']}\ndata: {json.dumps(event['data'])}\n\n"
                    break
                yield f"event: {event['event']}\ndata: {json.dumps(event['data'])}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            cleanup(task_id)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/map-reduce")
@limiter.limit("10/minute")
async def create_map_reduce(request: Request, body: dict):
    root_task = body.get("root_task", "")
    if not root_task.strip():
        return JSONResponse({"error": "root_task required"}, status_code=400)
    map_description = body.get("map_description", "Process the following input")
    raw_par = body.get("parallelism", 3)
    if not isinstance(raw_par, int) or raw_par < 1 or raw_par > 10:
        return JSONResponse({"error": "parallelism must be int in [1, 10]"}, status_code=400)
    parallelism = raw_par
    reduce_description = body.get("reduce_description")

    graph = TaskGraph.create_map_reduce(
        root_task=root_task,
        map_description=map_description,
        parallelism=parallelism,
        reduce_description=reduce_description,
    )

    _prune_old()
    _graphs[graph.id] = graph
    asyncio.create_task(execute_graph(graph))

    return JSONResponse({
        "task_id": graph.id,
        "type": "map-reduce",
        "parallelism": parallelism,
        "status": graph.status.value,
        "subtasks": [
            {"id": st.id, "description": st.description[:80], "agent_type": st.agent_type,
             "depends_on": st.depends_on, "status": st.status.value}
            for st in graph.subtasks
        ],
    }, status_code=201)


@router.get("/agents")
@limiter.limit("30/minute")
async def list_agents(request: Request):
    profiles = pool.list_profiles()
    return JSONResponse([
        {
            "type": p.agent_type,
            "capabilities": p.capabilities,
            "estimated_cost_per_token": p.estimated_cost_per_token,
            "max_concurrency": p.max_concurrency,
            "available": p.available,
            "health": {"status": p.health_status, "last_check": p.health_last_check},
        }
        for p in profiles
    ])


def _prune_old():
    if len(_graphs) > _MAX_GRAPHS:
        sorted_ids = sorted(_graphs.keys(), key=lambda gid: _graphs[gid].created_at)
        for gid in sorted_ids[:len(_graphs) - _MAX_GRAPHS]:
            cleanup(gid)
            _graphs.pop(gid, None)
