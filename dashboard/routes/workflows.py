from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from loguru import logger

from dashboard.rate_limit import limiter
from dashboard.workflow import WorkflowEngine, parse_workflow

router = APIRouter(prefix="/api/workflows", tags=["workflows"])

DATA_DIR = Path(__file__).parent.parent / "data"
WORKFLOWS_DIR = DATA_DIR / "workflows"


def _ensure_dir() -> None:
    WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)


@router.get("")
@limiter.limit("30/minute")
async def list_workflows(request: Request) -> list[dict]:
    _ensure_dir()
    workflows = []
    for f in sorted(WORKFLOWS_DIR.iterdir()):
        if f.suffix in (".json", ".yaml", ".yml"):
            try:
                wf = parse_workflow(f)
                workflows.append({"name": wf.name, "file": f.name, "steps": len(wf.steps)})
            except ValueError as exc:
                workflows.append({"name": f.stem, "file": f.name, "error": str(exc)})
    return workflows


@router.post("/load")
@limiter.limit("10/minute")
async def load_workflow(request: Request) -> dict:
    body = await request.json()
    source = body.get("source", "")
    if not source:
        raise HTTPException(400, "source is required")

    try:
        wf = parse_workflow(source)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    _ensure_dir()
    path = WORKFLOWS_DIR / f"{wf.name}.json"
    path.write_text(json.dumps({
        "name": wf.name,
        "description": wf.description,
        "steps": [
            {
                "id": s.id,
                "description": s.description,
                "agent": s.agent,
                "depends_on": s.depends_on,
                "approval_gate": s.approval_gate,
            }
            for s in wf.steps
        ],
    }, indent=2))
    logger.info("Saved workflow {} ({} steps)", wf.name, len(wf.steps))
    return {"name": wf.name, "steps": len(wf.steps)}


@router.get("/{name}")
@limiter.limit("30/minute")
async def get_workflow(request: Request, name: str) -> dict:
    _ensure_dir()
    for ext in (".json", ".yaml", ".yml"):
        path = WORKFLOWS_DIR / f"{name}{ext}"
        if path.exists():
            wf = parse_workflow(path)
            return {
                "name": wf.name,
                "description": wf.description,
                "steps": [s.__dict__ for s in wf.steps],
            }
    raise HTTPException(404, f"Workflow '{name}' not found")


@router.post("/{name}/execute")
@limiter.limit("10/minute")
async def execute_workflow(request: Request, name: str) -> dict:
    _ensure_dir()
    body = await request.json()
    session_id = body.get("session_id", "default")

    path = None
    for ext in (".json", ".yaml", ".yml"):
        candidate = WORKFLOWS_DIR / f"{name}{ext}"
        if candidate.exists():
            path = candidate
            break
    if path is None:
        raise HTTPException(404, f"Workflow '{name}' not found")

    wf = parse_workflow(path)
    engine = WorkflowEngine(wf, session_id)
    ready = engine.ready_steps()

    return {
        "workflow": wf.name,
        "total_steps": len(wf.steps),
        "ready_steps": [s.id for s in ready],
        "blocked_steps": [
            s.id for s in wf.steps
            if s.status == "pending" and s not in ready
        ],
        "done": engine.all_done(),
    }


@router.get("/{name}/status")
@limiter.limit("30/minute")
async def workflow_status(request: Request, name: str) -> dict:
    _ensure_dir()
    path = None
    for ext in (".json", ".yaml", ".yml"):
        candidate = WORKFLOWS_DIR / f"{name}{ext}"
        if candidate.exists():
            path = candidate
            break
    if path is None:
        raise HTTPException(404, f"Workflow '{name}' not found")
    wf = parse_workflow(path)
    return {
        "name": wf.name,
        "steps": [s.__dict__ for s in wf.steps],
    }
