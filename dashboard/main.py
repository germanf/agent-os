from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from dashboard import chat_store
from dashboard.config import FRONTEND_DIST
from dashboard.headroom_sidecar import start as start_headroom
from dashboard.hermes_adapter import init_kanban
from dashboard.kanban_feedback import start as start_kanban_feedback
from dashboard.log import configure_logging
from dashboard.middleware.auth import AuthMiddleware
from dashboard.middleware.hsts import HSTSHeaderMiddleware
from dashboard.rate_limit import limiter
from dashboard.routes.agents import router as agents_router
from dashboard.routes.backends import router as backends_router
from dashboard.routes.chats import router as chats_router
from dashboard.routes.diagnostics import router as diagnostics_router
from dashboard.routes.jobs import router as jobs_router
from dashboard.routes.kanban import router as kanban_router
from dashboard.routes.notes import router as notes_router
from dashboard.routes.projects import router as projects_router

app = FastAPI(title="Agentic Software Boutique")
app.state.limiter = limiter

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(AuthMiddleware)
app.add_middleware(HSTSHeaderMiddleware)

app.include_router(agents_router)
app.include_router(jobs_router)
app.include_router(kanban_router)
app.include_router(backends_router)
app.include_router(notes_router)
app.include_router(projects_router)
app.include_router(chats_router)
app.include_router(diagnostics_router)


@app.on_event("startup")
async def startup():
    configure_logging()
    await start_headroom()
    await chat_store.init_db()
    await init_kanban()
    start_kanban_feedback()


if (FRONTEND_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")


@app.get("/{full_path:path}")
async def spa_fallback(full_path: str):
    index_path = FRONTEND_DIST / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return JSONResponse(status_code=200, content={"status": "API running — frontend not built"})
