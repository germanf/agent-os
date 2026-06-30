from fastapi import APIRouter, HTTPException, Request

from dashboard.kanban import block_task, complete_task, create_task, list_tasks, show_task, unblock_task
from dashboard.kanban_feedback import poll_once as poll_feedback_once
from dashboard.models.schemas import KanbanCreateRequest
from dashboard.rate_limit import limiter

router = APIRouter(prefix="/api/kanban", tags=["kanban"])


@router.get("/tasks")
@limiter.limit("30/minute")
async def get_tasks(request: Request, status: str | None = None, tenant: str | None = None):
    return await list_tasks(status=status, tenant=tenant)


@router.post("/tasks")
@limiter.limit("10/minute")
async def create_new_task(request: Request, body: KanbanCreateRequest):
    task = await create_task(
        title=body.title,
        body=body.body,
        assignee=body.assignee,
        priority=body.priority,
        tenant=body.tenant,
    )
    if task is None:
        raise HTTPException(status_code=500, detail="Failed to create task")
    return task


@router.get("/tasks/{task_id}")
@limiter.limit("30/minute")
async def get_task(request: Request, task_id: str):
    task = await show_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/tasks/{task_id}/complete")
@limiter.limit("10/minute")
async def complete_existing_task(request: Request, task_id: str):
    ok = await complete_task(task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found or could not complete")
    return {"ok": True}


@router.post("/tasks/{task_id}/block")
@limiter.limit("10/minute")
async def block_existing_task(request: Request, task_id: str, reason: str = "Blocked via API"):
    ok = await block_task(task_id, reason)
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found or could not block")
    return {"ok": True}


@router.post("/tasks/{task_id}/unblock")
@limiter.limit("10/minute")
async def unblock_existing_task(request: Request, task_id: str):
    ok = await unblock_task(task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found or could not unblock")
    return {"ok": True}


@router.post("/feedback/poll")
@limiter.limit("6/minute")
async def poll_now(request: Request):
    await poll_feedback_once()
    return {"ok": True}
