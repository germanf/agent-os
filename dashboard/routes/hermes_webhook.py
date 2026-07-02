from typing import Any

from fastapi import APIRouter, Request
from loguru import logger
from pydantic import BaseModel

from dashboard import approvals as approvals_db
from dashboard.rate_limit import limiter

router = APIRouter(prefix="/api/hermes", tags=["hermes-webhook"])


class WebhookEvent(BaseModel):
    event: str
    task_id: str | None = None
    tenant: str | None = None
    title: str | None = None
    payload: dict[str, Any] | None = None


@router.post("/webhook")
@limiter.limit("60/minute")
async def receive_event(request: Request, evt: WebhookEvent):
    logger.info("Hermes webhook received: {} task={}", evt.event, evt.task_id)
    if evt.event == "task.review" and evt.task_id:
        approval = await approvals_db.create_approval(
            kanban_task_id=evt.task_id,
            kanban_tenant=evt.tenant,
            task_title=evt.title,
        )
        return {"ok": True, "approval_id": approval["id"] if approval else None}
    return {"ok": True, "noop": True}
