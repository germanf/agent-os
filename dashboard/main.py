"""Agentic Software Boutique — FastAPI backend."""

from __future__ import annotations

import asyncio
import base64
import logging
import os
import secrets
import sys
from pathlib import Path

import backends
import chat_store
import config
import runner as runner_mod
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from runner import cancel_job, create_job, get_job, get_logs, list_jobs, run_job, stream_logs
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────────

BASE_DIR  = Path(__file__).parent
ROOT_DIR  = BASE_DIR.parent
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
UPLOADS_DIR = BASE_DIR / "data" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
VAULT_DIR = Path(config.VAULT_DIR)  # only exists on the production VM


# ── HTTP Basic Auth ─────────────────────────────────────────────────────────────

def _get_auth_credentials() -> tuple[str, str]:
    """Load HTTP Basic Auth credentials from environment variables.

    Returns ("", "") if credentials are not configured (callers handle 401).
    """
    username = os.environ.get("DASH_USER", "").strip()
    password = os.environ.get("DASH_PASS", "").strip()

    if not username or not password:
        logger.warning("HTTP Auth credentials not configured (DASH_USER/DASH_PASS env vars missing)")
        return "", ""

    return username, password


def _verify_credentials(credentials: HTTPBasicCredentials) -> bool:
    """Verify HTTP Basic Auth credentials using timing-safe comparison."""
    expected_user, expected_pass = _get_auth_credentials()
    if not expected_user or not expected_pass:
        return False
    # Use secrets.compare_digest for timing-safe comparison
    user_match = secrets.compare_digest(credentials.username, expected_user)
    pass_match = secrets.compare_digest(credentials.password, expected_pass)
    return user_match and pass_match


# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(title="Agentic Software Boutique")
security = HTTPBasic()

# ── Rate Limiting ──────────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, headers_enabled=False)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Rate limit exceeded handler with proper headers."""
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"},
        headers={
            "Retry-After": "60",
            "X-RateLimit-Limit": "60",
            "X-RateLimit-Remaining": "0",
        }
    )


@app.on_event("startup")
async def startup_event():
    """Initialize database on app startup."""
    await chat_store.init_db()


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce HTTP Basic Auth on protected routes.

    Allows public access to:
    - /api/health (health check endpoint)

    All other routes require valid Basic Auth credentials.
    """

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/api/health":
            return await call_next(request)

        # Extract and verify credentials
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Basic "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized"},
                headers={"WWW-Authenticate": "Basic realm=\"Dashboard\""},
            )

        try:
            # Parse Basic Auth header: "Basic base64(username:password)"
            encoded = auth_header[6:]  # Remove "Basic " prefix
            decoded = base64.b64decode(encoded).decode("utf-8")
            username, password = decoded.split(":", 1)
            credentials = HTTPBasicCredentials(username=username, password=password)
        except (ValueError, base64.binascii.Error, UnicodeDecodeError):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid credentials format"},
                headers={"WWW-Authenticate": "Basic realm=\"Dashboard\""},
            )

        if not _verify_credentials(credentials):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid credentials"},
                headers={"WWW-Authenticate": "Basic realm=\"Dashboard\""},
            )

        return await call_next(request)


app.add_middleware(AuthMiddleware)

# ── Security: HSTS Middleware ──────────────────────────────────────────────────
# Adds Strict-Transport-Security header to all responses.
# This is redundant with nginx HSTS but serves as a fallback / defense-in-depth.
# Note: with self-signed certs, browsers ignore HSTS on cert errors (RFC 6797 sec 7.4).
@app.middleware("http")
async def add_hsts_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# ── Job management ─────────────────────────────────────────────────────────────

@app.get("/api/jobs")
@limiter.limit("30/minute")
async def get_jobs(request: Request):
    return list_jobs()


@app.get("/api/jobs/{job_id}")
@limiter.limit("30/minute")
async def get_job_status(request: Request, job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job.to_dict()


@app.get("/api/jobs/{job_id}/logs")
@limiter.limit("30/minute")
async def get_job_logs(request: Request, job_id: str):
    return get_logs(job_id)


@app.get("/api/jobs/{job_id}/stream")
@limiter.limit("30/minute")
async def stream_job_logs(request: Request, job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return StreamingResponse(
        stream_logs(job),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/jobs/{job_id}/cancel")
@limiter.limit("30/minute")
async def cancel_job_endpoint(request: Request, job_id: str):
    ok = await cancel_job(job_id)
    if not ok:
        raise HTTPException(400, "Job not running or not found")
    return {"ok": True}


@app.get("/api/jobs/{job_id}/events")
@limiter.limit("30/minute")
async def stream_job_events(request: Request, job_id: str):
    """SSE endpoint that streams normalized events (tool-agnostic) instead of raw lines."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    backend = backends.get(job.tool)
    if not backend:
        raise HTTPException(400, f"No backend registered for tool '{job.tool}'")

    async def event_generator():
        snapshot = list(job._log_lines)
        queue: asyncio.Queue = asyncio.Queue()
        still_running = job.status in (runner_mod.Status.QUEUED, runner_mod.Status.RUNNING)
        if still_running:
            job._subscribers.append(queue)

        # Replay existing lines through the backend parser
        for line in snapshot:
            evt = backend.parse_line(line)
            if evt:
                yield _format_sse_event(evt)

        if not still_running:
            yield "event: done\ndata: {}\n\n"
            return

        try:
            while True:
                try:
                    line = await asyncio.wait_for(queue.get(), timeout=25)
                except TimeoutError:
                    yield "event: ping\ndata: {}\n\n"
                    continue
                if line is None:
                    break
                evt = backend.parse_line(line)
                if evt:
                    yield _format_sse_event(evt)
        finally:
            if queue in job._subscribers:
                job._subscribers.remove(queue)

        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/backends")
@limiter.limit("30/minute")
async def list_backends(request: Request):
    """List available chat backends."""
    return {
        "available": backends.list_available(),
        "all": backends.list_all_registered(),
    }


def _format_sse_event(evt) -> str:
    """Serialize a NormalizedEvent to an SSE data line."""
    import dataclasses
    import json as _json
    payload = _json.dumps(dataclasses.asdict(evt), default=str)
    return f"data: {payload}\n\n"


# ── Notes (vault de Obsidian) ─────────────────────────────────────────────────

def _build_note_tree(directory: Path) -> list[dict]:
    entries = []
    for entry in sorted(directory.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
        if entry.is_dir():
            entries.append({
                "name": entry.name,
                "path": str(entry.relative_to(VAULT_DIR)),
                "type": "dir",
                "children": _build_note_tree(entry),
            })
        elif entry.suffix == ".md":
            entries.append({
                "name": entry.name,
                "path": str(entry.relative_to(VAULT_DIR)),
                "type": "file",
            })
    return entries


@app.get("/api/notes/tree")
@limiter.limit("30/minute")
async def get_notes_tree(request: Request):
    if not VAULT_DIR.exists():
        return []
    return _build_note_tree(VAULT_DIR)


@app.get("/api/notes/content")
@limiter.limit("30/minute")
async def get_note_content(request: Request, path: str):
    rel = Path(path)
    if rel.is_absolute() or ".." in rel.parts or rel.suffix != ".md":
        raise HTTPException(400, "Ruta inválida")
    full = (VAULT_DIR / rel).resolve()
    if not full.is_relative_to(VAULT_DIR.resolve()) or not full.exists():
        raise HTTPException(404, "Nota no encontrada")
    return {"path": path, "content": full.read_text()}


# ── Chat: projects ────────────────────────────────────────────────────────────

class ProjectCreateRequest(BaseModel):
    name: str
    system_prompt: str | None = None


class ProjectUpdateRequest(BaseModel):
    name: str | None = None
    system_prompt: str | None = None


class ProjectFolderRequest(BaseModel):
    path: str


@app.get("/api/projects")
@limiter.limit("30/minute")
async def list_projects_endpoint(request: Request):
    return await chat_store.list_projects()


@app.post("/api/projects")
@limiter.limit("30/minute")
async def create_project_endpoint(request: Request, req: ProjectCreateRequest):
    return await chat_store.create_project(req.name, req.system_prompt)


@app.patch("/api/projects/{project_id}")
@limiter.limit("30/minute")
async def update_project_endpoint(request: Request, project_id: int, req: ProjectUpdateRequest):
    project = await chat_store.update_project(project_id, req.name, req.system_prompt)
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@app.delete("/api/projects/{project_id}")
@limiter.limit("30/minute")
async def delete_project_endpoint(request: Request, project_id: int):
    if not await chat_store.delete_project(project_id):
        raise HTTPException(404, "Project not found")
    return {"ok": True}


@app.post("/api/projects/{project_id}/folders")
@limiter.limit("30/minute")
async def add_project_folder_endpoint(request: Request, project_id: int, req: ProjectFolderRequest):
    if not await chat_store.get_project(project_id):
        raise HTTPException(404, "Project not found")
    if not os.path.isdir(req.path):
        raise HTTPException(400, "La carpeta no existe en este servidor")
    return await chat_store.add_project_folder(project_id, req.path)


@app.delete("/api/projects/folders/{folder_id}")
@limiter.limit("30/minute")
async def remove_project_folder_endpoint(request: Request, folder_id: int):
    if not await chat_store.remove_project_folder(folder_id):
        raise HTTPException(404, "Folder not found")
    return {"ok": True}


# ── Chat: chats (history) ────────────────────────────────────────────────────

class ChatCreateRequest(BaseModel):
    id: str | None = None
    project_id: int | None = None


class ChatRenameRequest(BaseModel):
    title: str


@app.get("/api/chats")
@limiter.limit("30/minute")
async def list_chats_endpoint(request: Request, project_id: int | None = None):
    return await chat_store.list_chats(project_id)


@app.post("/api/chats")
@limiter.limit("30/minute")
async def create_chat_endpoint(request: Request, req: ChatCreateRequest):
    return await chat_store.create_chat(chat_id=req.id, project_id=req.project_id)


@app.get("/api/chats/{chat_id}")
@limiter.limit("30/minute")
async def get_chat_endpoint(request: Request, chat_id: str):
    chat = await chat_store.get_chat(chat_id)
    if not chat:
        raise HTTPException(404, "Chat not found")
    chat["messages"] = await chat_store.list_messages(chat_id)
    return chat


@app.patch("/api/chats/{chat_id}")
@limiter.limit("30/minute")
async def rename_chat_endpoint(request: Request, chat_id: str, req: ChatRenameRequest):
    if not await chat_store.rename_chat(chat_id, req.title):
        raise HTTPException(404, "Chat not found")
    return {"ok": True}


@app.delete("/api/chats/{chat_id}")
@limiter.limit("30/minute")
async def delete_chat_endpoint(request: Request, chat_id: str):
    if not await chat_store.delete_chat(chat_id):
        raise HTTPException(404, "Chat not found")
    return {"ok": True}


# ── Chat: send a message ──────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str
    message: str
    first: bool = False
    project_id: int | None = None
    file_paths: list[str] | None = None


async def _get_backend_for_chat(chat_id: str | None) -> backends.ChatBackend:
    """Get the backend for a chat, falling back to the selected backend."""
    if chat_id:
        chat = await chat_store.get_chat(chat_id)
        if chat and chat.get("tool_backend"):
            b = backends.get(chat["tool_backend"])
            if b:
                return b
    return backends.select_backend()


def _auto_title(text: str, limit: int = 50) -> str:
    text = " ".join(text.split())
    return text[:limit] + ("…" if len(text) > limit else "")





async def _run_chat_job(job: runner_mod.Job, chat_id: str) -> None:
    try:
        await run_job(job)
        backend = backends.get(job.tool)
        if not backend:
            logger.warning("Unknown backend '%s' for job %s", job.tool, job.id)
            return
        text, tool_calls = backend.parse_full_transcript(job._log_lines)
        if not text and not tool_calls:
            return
        await chat_store.add_message(chat_id, "assistant", text, tool_calls or None)
        await chat_store.touch_chat(chat_id)
        chat = await chat_store.get_chat(chat_id)
        if chat and not chat["title"]:
            await chat_store.rename_chat(chat_id, _auto_title(text))
    except Exception:
        logger.exception("Chat job failed for chat_id=%s", chat_id)


@app.post("/api/chat/send")
@limiter.limit("10/minute")
async def chat_send(request: Request, req: ChatRequest, bg: BackgroundTasks):
    if not await chat_store.get_chat(req.session_id):
        raise HTTPException(404, "Chat not found — create it first via POST /api/chats")
    await chat_store.add_message(req.session_id, "user", req.message)

    backend = await _get_backend_for_chat(req.session_id)
    project = None
    if req.project_id is not None:
        project = await chat_store.get_project(req.project_id)

    context_dirs = [str(VAULT_DIR)] if VAULT_DIR.exists() else []

    cmd = backend.build_command(
        message=req.message,
        session_id=req.session_id,
        first=req.first,
        project=project,
        file_paths=req.file_paths,
        context_dirs=context_dirs,
    )
    job = create_job(backend.name, cmd, cwd=str(ROOT_DIR))
    bg.add_task(_run_chat_job, job, req.session_id)
    return {"job_id": job.id, "tool_backend": backend.name}


@app.post("/api/files/upload")
@limiter.limit("3/minute")
async def upload_files(request: Request, chat_id: str = Query(...), files: list[UploadFile] = File(...)):
    if not await chat_store.get_chat(chat_id):
        raise HTTPException(404, "Chat not found")

    # ── Phase 1: Count validation (cheapest, no I/O) ──────────────────────────────
    if len(files) > config.MAX_FILES:
        raise HTTPException(
            400,
            f"Demasiados archivos. Máximo {config.MAX_FILES} archivos por envío."
        )

    # ── Phase 2: Size validation (before any writes) ──────────────────────────────
    total_size = 0
    for file in files:
        # file.size is populated by Starlette for multipart uploads
        file_size = file.size if file.size is not None else 0
        if file_size > config.MAX_FILE_SIZE:
            max_mb = config.MAX_FILE_SIZE // (1024 * 1024)
            raise HTTPException(
                413,
                f"El archivo '{file.filename}' es demasiado grande. Máximo {max_mb} MB por archivo.",
            )
        total_size += file_size

    if total_size > config.MAX_TOTAL_SIZE:
        max_mb = config.MAX_TOTAL_SIZE // (1024 * 1024)
        raise HTTPException(
            413,
            f"El tamaño total de los archivos excede el límite. Máximo {max_mb} MB en total.",
        )

    # ── Phase 3: Write files (after all validations pass) ──────────────────────────
    chat_upload_dir = UPLOADS_DIR / chat_id
    chat_upload_dir.mkdir(parents=True, exist_ok=True)

    file_paths = []
    for file in files:
        if not file.filename:
            continue
        filename = Path(file.filename).name
        filepath = chat_upload_dir / filename
        try:
            with open(filepath, "wb") as f:
                content = await file.read()
                f.write(content)
            file_paths.append(str(filepath))
        except Exception as e:
            raise HTTPException(400, f"Error al guardar {file.filename}: {e}")

    # TODO (future work): Implement cleanup of uploaded files when chat is deleted
    return {"file_paths": file_paths}


# ── Diagnostics ────────────────────────────────────────────────────────────────

@app.get("/api/health")
@limiter.limit("60/minute")
async def health_check(request: Request):
    """Simple health check endpoint."""
    return {"status": "ok", "timestamp": __import__('time').time()}


@app.get("/api/diagnostics")
@limiter.limit("30/minute")
async def diagnostics(request: Request):
    """Detailed diagnostics for debugging deployment issues."""
    diagnostics_data = {}

    # Check if frontend is built
    diagnostics_data["frontend_exists"] = (FRONTEND_DIST / "index.html").exists()
    diagnostics_data["frontend_dist_path"] = str(FRONTEND_DIST)

    # Check if database exists
    diagnostics_data["database_exists"] = chat_store.DB_PATH.exists()
    diagnostics_data["database_path"] = str(chat_store.DB_PATH)

    # Check if vault exists (production only)
    diagnostics_data["vault_exists"] = VAULT_DIR.exists()
    diagnostics_data["vault_path"] = str(VAULT_DIR)

    # Python version
    diagnostics_data["python_version"] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    # uvicorn and FastAPI versions
    import fastapi
    import uvicorn as _uvicorn
    diagnostics_data["fastapi_version"] = fastapi.__version__
    diagnostics_data["uvicorn_version"] = _uvicorn.__version__

    return diagnostics_data


# ── Frontend SPA (Vite build) ───────────────────────────────────────────────────
# Must be defined last: FastAPI matches routes in registration order, and this
# catch-all would otherwise shadow every /api/* and /auth/* route above it.

if (FRONTEND_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="frontend-assets")


@app.get("/{full_path:path}")
async def spa_fallback(full_path: str):
    index = FRONTEND_DIST / "index.html"
    if not index.exists():
        raise HTTPException(404, "Frontend no compilado — correr npm run build en dashboard/frontend")
    return FileResponse(index)
