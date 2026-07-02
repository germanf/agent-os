from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from dashboard import cron_adapter
from dashboard.rate_limit import limiter

router = APIRouter(prefix="/api/cron", tags=["cron"])


class CronCreateRequest(BaseModel):
    name: str
    schedule: str
    prompt: str | None = None
    script: str | None = None
    deliver: str | None = None
    workdir: str | None = None
    no_agent: bool = False


@router.get("/jobs")
@limiter.limit("30/minute")
async def list_cron_jobs(request: Request, all: bool = False):
    text = await cron_adapter.list_jobs(include_all=all)
    return {"raw": text}


@router.post("/jobs")
@limiter.limit("10/minute")
async def create_cron_job(request: Request, body: CronCreateRequest):
    code, out, err = await cron_adapter.create_job(
        schedule=body.schedule,
        prompt=body.prompt,
        name=body.name,
        script=body.script,
        deliver=body.deliver,
        workdir=body.workdir,
        no_agent=body.no_agent,
    )
    if code != 0:
        raise HTTPException(status_code=500, detail=err or out or "Failed to create cron job")
    return {"ok": True, "output": out}


@router.post("/jobs/{name}/pause")
@limiter.limit("10/minute")
async def pause_job(request: Request, name: str):
    code, out, err = await cron_adapter.pause_job(name)
    if code != 0:
        raise HTTPException(status_code=500, detail=err or out)
    return {"ok": True}


@router.post("/jobs/{name}/resume")
@limiter.limit("10/minute")
async def resume_job(request: Request, name: str):
    code, out, err = await cron_adapter.resume_job(name)
    if code != 0:
        raise HTTPException(status_code=500, detail=err or out)
    return {"ok": True}


@router.post("/jobs/{name}/run-now")
@limiter.limit("10/minute")
async def run_job(request: Request, name: str):
    code, out, err = await cron_adapter.run_now(name)
    if code != 0:
        raise HTTPException(status_code=500, detail=err or out)
    return {"ok": True}


@router.delete("/jobs/{name}")
@limiter.limit("10/minute")
async def remove_job(request: Request, name: str):
    code, out, err = await cron_adapter.remove_job(name)
    if code != 0:
        raise HTTPException(status_code=500, detail=err or out)
    return {"ok": True}


@router.post("/tick")
@limiter.limit("6/minute")
async def tick_now(request: Request):
    code, out, err = await cron_adapter.tick()
    return {"ok": code == 0, "exit_code": code, "output": out, "error": err}


@router.get("/status")
@limiter.limit("30/minute")
async def cron_status(request: Request):
    code, out, err = await cron_adapter.status()
    return {"exit_code": code, "status": out, "error": err}
