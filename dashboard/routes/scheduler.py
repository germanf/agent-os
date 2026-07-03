from fastapi import APIRouter, Request
from pydantic import BaseModel

from dashboard.chat_store import _connect
from dashboard.ops_workflows import list_workflows
from dashboard.rate_limit import limiter
from dashboard.workflow_scheduler import _pending_retries, tick_one

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])


@router.get("/workflows")
@limiter.limit("30/minute")
async def get_workflows(request: Request):
    return list_workflows()


@router.post("/tick")
@limiter.limit("10/minute")
async def trigger_tick(request: Request):
    from dashboard.workflow_scheduler import tick
    await tick()
    return {"ok": True}


class RunRequest(BaseModel):
    name: str


@router.post("/run")
@limiter.limit("10/minute")
async def run_workflow(request: Request, body: RunRequest):
    return await tick_one(body.name)


@router.get("/runs")
@limiter.limit("30/minute")
async def get_runs(request: Request, limit: int = 20):
    async with _connect() as conn:
        cur = await conn.execute(
            "SELECT * FROM workflow_runs ORDER BY started_at DESC LIMIT ?", (limit,)
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


@router.get("/retries")
@limiter.limit("30/minute")
async def get_retries(request: Request):
    return {
        name: not t.done()
        for name, t in list(_pending_retries.items())
    }
