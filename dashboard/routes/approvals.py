from fastapi import APIRouter, HTTPException, Request

from dashboard import approvals as approvals_db
from dashboard.kanban import (
    comment_task as kanban_comment,
)
from dashboard.kanban import (
    complete_task as kanban_complete,
)
from dashboard.kanban import (
    unblock_task as kanban_unblock,
)
from dashboard.kanban_feedback import poll_once as poll_feedback_once
from dashboard.rate_limit import limiter

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


@router.get("/pending")
@limiter.limit("30/minute")
async def get_pending(request: Request):
    return await approvals_db.list_pending()


@router.post("/{approval_id}/approve")
@limiter.limit("10/minute")
async def approve_task(request: Request, approval_id: int, by: str = "user"):
    approval = await approvals_db.get_approval(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval["status"] != "pending":
        raise HTTPException(status_code=400, detail="Already decided")

    task_id = approval["kanban_task_id"]
    await kanban_unblock(task_id)
    await kanban_comment(
        task_id, f"Approved by {by} (id={approval_id})"
    )
    decided = await approvals_db.decide(approval_id, "approved", decided_by=by)
    await poll_feedback_once()
    return decided


@router.post("/{approval_id}/deny")
@limiter.limit("10/minute")
async def deny_task(request: Request, approval_id: int, reason: str = "", by: str = "user"):
    approval = await approvals_db.get_approval(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval["status"] != "pending":
        raise HTTPException(status_code=400, detail="Already decided")

    task_id = approval["kanban_task_id"]
    note = f"Denied by {by}"
    if reason:
        note += f": {reason}"
    await kanban_comment(task_id, note)
    decided = await approvals_db.decide(approval_id, "denied", decided_by=by)
    await poll_feedback_once()
    return decided


@router.post("/{approval_id}/complete-task")
@limiter.limit("10/minute")
async def complete_after_approval(request: Request, approval_id: int, by: str = "user"):
    approval = await approvals_db.get_approval(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval["decision"] != "approved":
        raise HTTPException(status_code=400, detail="Approval not approved")

    task_id = approval["kanban_task_id"]
    await kanban_complete(task_id)
    await poll_feedback_once()
    return {"ok": True}
