from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from dashboard import chat_store
from dashboard.approvals import init_approvals
from dashboard.checkpoints import CheckpointStore, init_checkpoints
from dashboard.config import FRONTEND_DIST
from dashboard.cron_loop import start as start_cron_loop
from dashboard.headroom_sidecar import start as start_headroom
from dashboard.hermes_adapter import init_kanban
from dashboard.kanban_feedback import start as start_kanban_feedback
from dashboard.log import configure_logging
from dashboard.memory import init_memory
from dashboard.middleware.auth import AuthMiddleware
from dashboard.middleware.hsts import HSTSHeaderMiddleware
from dashboard.rate_limit import limiter
from dashboard.routes.agents import router as agents_router
from dashboard.routes.approvals import router as approvals_router
from dashboard.routes.backends import router as backends_router
from dashboard.routes.chats import router as chats_router
from dashboard.routes.cron import router as cron_router
from dashboard.routes.diagnostics import router as diagnostics_router
from dashboard.routes.hermes_webhook import router as hermes_webhook_router
from dashboard.routes.jobs import router as jobs_router
from dashboard.routes.kanban import router as kanban_router
from dashboard.routes.notes import router as notes_router
from dashboard.routes.projects import router as projects_router
from dashboard.routes.token_accounting import router as token_accounting_router
from dashboard.routes.workflows import router as workflows_router
from dashboard.token_accounting import init_token_accounting
from dashboard.tracing import TracingMiddleware

app = FastAPI(title="Agentic Software Boutique")
app.state.limiter = limiter

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(AuthMiddleware)
app.add_middleware(HSTSHeaderMiddleware)
app.add_middleware(TracingMiddleware)

app.include_router(agents_router)
app.include_router(jobs_router)
app.include_router(kanban_router)
app.include_router(backends_router)
app.include_router(notes_router)
app.include_router(projects_router)
app.include_router(chats_router)
app.include_router(diagnostics_router)
app.include_router(approvals_router)
app.include_router(hermes_webhook_router)
app.include_router(cron_router)
app.include_router(workflows_router)
app.include_router(token_accounting_router)


@app.on_event("startup")
async def startup():
    configure_logging()
    await start_headroom()
    await chat_store.init_db()
    await init_kanban()
    await init_token_accounting()
    await init_approvals()
    await init_checkpoints()
    await init_memory()
    start_kanban_feedback()
    start_cron_loop()
    store = CheckpointStore()
    orphaned = await store.mark_orphans()
    if orphaned:
        from loguru import logger as _logger
        _logger.info("Marked {} job checkpoints as orphans on startup", orphaned)


if (FRONTEND_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")


@app.get("/{full_path:path}")
async def spa_fallback(full_path: str):
    index_path = FRONTEND_DIST / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return JSONResponse(status_code=200, content={"status": "API running — frontend not built"})
