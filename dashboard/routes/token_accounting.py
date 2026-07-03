import time

from fastapi import APIRouter, Request

from dashboard.models.schemas import TokenLogRequest
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
async def log_usage(request: Request, body: TokenLogRequest):
    result = await _accountant.log_usage(
        session_id=body.session_id,
        prompt_tokens=body.prompt_tokens,
        completion_tokens=body.completion_tokens,
        project_id=body.project_id,
        agent_name=body.agent_name,
        model=body.model,
    )
    return result


@router.get("/summary")
@limiter.limit("30/minute")
async def usage_summary(request: Request, project_id: int | None = None, since_hours: int | None = None):
    since = (time.time() - since_hours * 3600) if since_hours else None
    rows = await _accountant.summary(project_id=project_id, since=since)
    return rows
