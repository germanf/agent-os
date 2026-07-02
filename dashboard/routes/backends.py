from fastapi import APIRouter, Request

from dashboard.backends import discover, list_all_registered
from dashboard.models.schemas import BackendInfo
from dashboard.rate_limit import limiter

router = APIRouter(prefix="/api", tags=["backends"])


@router.get("/backends", response_model=list[BackendInfo])
@limiter.limit("30/minute")
async def list_backends(request: Request):
    available = set(discover().keys())
    all_registered = list_all_registered()
    return [
        BackendInfo(
            id=name,
            name=name.title(),
            description=f"{name} backend ({'available' if name in available else 'unavailable'})",
        )
        for name in all_registered
    ]
