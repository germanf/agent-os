import time

from fastapi import APIRouter, HTTPException, Request

from dashboard.rate_limit import limiter
from dashboard.token_accounting import TokenAccountant

router = APIRouter(prefix="/api/tokens", tags=["token_accounting"])

_accountant = TokenAccountant()


@router.get("")
@limiter.limit("30/minute")
async def list_usage(
    request: Request,
    project_id: int | None = None,
    session_id: str | None = None,
    limit: int = 100,
):
    items = await _accountant.list(project_id=project_id, session_id=session_id, limit=limit)
    return items


@router.post("")
@limiter.limit("30/minute")
async def log_usage(request: Request):
    body = await request.json()
    session_id = body.get("session_id", "")
    if not session_id:
        raise HTTPException(400, "session_id is required")
    result = await _accountant.log_usage(
        session_id=session_id,
        prompt_tokens=body.get("prompt_tokens", 0),
        completion_tokens=body.get("completion_tokens", 0),
        project_id=body.get("project_id"),
        agent_name=body.get("agent_name", "unknown"),
        model=body.get("model", "unknown"),
    )
    return result


@router.get("/summary")
@limiter.limit("30/minute")
async def usage_summary(request: Request, project_id: int | None = None, since_hours: int | None = None):
    since = (time.time() - since_hours * 3600) if since_hours else None
    rows = await _accountant.summary(project_id=project_id, since=since)
    return rows
