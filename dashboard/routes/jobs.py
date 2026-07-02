import asyncio

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from dashboard import runner
from dashboard.backends import get as get_backend
from dashboard.checkpoints import CheckpointStore
from dashboard.rate_limit import limiter
from dashboard.utils import format_sse_event

router = APIRouter(prefix="/api", tags=["jobs"])


# Static-path routes MUST be registered before the /jobs/{job_id} catch-all,
# otherwise FastAPI would match /jobs/orphans as job_id="orphans".
@router.get("/jobs/checkpoints")
@limiter.limit("30/minute")
async def list_checkpoints(request: Request):
    store = CheckpointStore()
    return await store.list_resumable()


@router.get("/jobs/orphans")
@limiter.limit("30/minute")
async def list_orphans(request: Request):
    store = CheckpointStore()
    return await store.list_orphans()


@router.post("/jobs/checkpoints/{cp_id}/resume")
@limiter.limit("10/minute")
async def resume_checkpoint(request: Request, cp_id: int):
    store = CheckpointStore()
    cp = await store.get(cp_id)
    if not cp:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    if cp.get("resumed"):
        raise HTTPException(status_code=409, detail="Checkpoint already resumed")

    job = runner.create_job(
        tool=cp["tool"],
        command=cp["command"],
        cwd=cp["cwd"],
        env=cp["env"],
    )
    asyncio.create_task(runner.run_job(job))
    await store.mark_resumed(cp_id)
    return {"ok": True, "job_id": job.id}


@router.get("/jobs")
@limiter.limit("30/minute")
async def list_jobs(request: Request):
    return runner.list_jobs()


@router.get("/jobs/{job_id}")
@limiter.limit("30/minute")
async def get_job(request: Request, job_id: str):
    job = runner.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_dict()


@router.get("/jobs/{job_id}/stream")
@limiter.limit("30/minute")
async def stream_job(request: Request, job_id: str):
    job = runner.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return StreamingResponse(runner.stream_logs(job), media_type="text/event-stream")


@router.get("/jobs/{job_id}/events")
@limiter.limit("30/minute")
async def stream_job_events(request: Request, job_id: str):
    job = runner.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    backend = get_backend(job.tool)
    snapshot = list(job._log_lines)
    queue: asyncio.Queue = asyncio.Queue()
    from dashboard.runner import Status
    still_running = job.status in (Status.QUEUED, Status.RUNNING)
    if still_running:
        job._subscribers.append(queue)

    async def event_stream():
        nonlocal snapshot
        for line in snapshot:
            ev = backend.parse_line(line) if backend else None
            if ev:
                yield format_sse_event(type(ev).__name__, {
                    k: v for k, v in ev.__dict__.items()
                })
        if not still_running:
            final = runner.get_job(job_id)
            yield format_sse_event("done", {
                "status": final.status if final else "evicted",
                "exit_code": final.exit_code if final else None,
            })
            return

        try:
            while True:
                try:
                    line = await asyncio.wait_for(queue.get(), timeout=25)
                except TimeoutError:
                    yield format_sse_event("ping", {})
                    continue
                if line is None:
                    break
                ev = backend.parse_line(line) if backend else None
                if ev:
                    yield format_sse_event(type(ev).__name__, {
                        k: v for k, v in ev.__dict__.items()
                    })
        finally:
            if queue in job._subscribers:
                job._subscribers.remove(queue)

        final = runner.get_job(job_id)
        yield format_sse_event("done", {
            "status": final.status if final else "evicted",
            "exit_code": final.exit_code if final else None,
        })

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/jobs/{job_id}/logs")
@limiter.limit("30/minute")
async def get_job_logs(request: Request, job_id: str):
    logs = runner.get_logs(job_id)
    return {"logs": logs}


@router.post("/jobs/{job_id}/cancel")
@limiter.limit("10/minute")
async def cancel_job(request: Request, job_id: str):
    success = await runner.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=409, detail="Job already finished or not found")
    return {"status": "cancelled"}


@router.post("/jobs/{job_id}/checkpoint")
@limiter.limit("10/minute")
async def checkpoint_job(request: Request, job_id: str):
    snapshot = runner.checkpoint_job(job_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Job not found")
    store = CheckpointStore()
    saved = await store.save(
        job_id=snapshot["id"],
        tool=snapshot["tool"],
        command=snapshot["command"],
        cwd=snapshot["cwd"],
        env=snapshot["env"],
        status=str(snapshot["status"]),
        exit_code=snapshot["exit_code"],
        started_at=snapshot["started_at"],
        ended_at=snapshot["ended_at"],
        logs=snapshot["logs"],
    )
    return {"ok": True, "checkpoint_id": saved["id"]}
