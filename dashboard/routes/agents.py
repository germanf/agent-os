from fastapi import APIRouter, Request

from dashboard.agents import list_agents
from dashboard.rate_limit import limiter

router = APIRouter(prefix="/api", tags=["agents"])


@router.get("/agents")
@limiter.limit("30/minute")
async def agents_list(request: Request):
    return list_agents()
