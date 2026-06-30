import asyncio

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse

from dashboard import chat_store, runner
from dashboard.backends import discover
from dashboard.backends import get as get_backend
from dashboard.config import BASE_DIR, UPLOADS_DIR
from dashboard.models.schemas import (
    ChatCreateRequest,
    ChatResponse,
    ChatSendRequest,
    ChatUpdateRequest,
    MessageResponse,
)
from dashboard.rate_limit import limiter

router = APIRouter(prefix="/api", tags=["chats"])


async def _get_backend_for_chat(chat: dict) -> str:
    tool_backend = chat.get("tool_backend") or "claude"
    available = discover()
    if tool_backend not in available:
        if available:
            tool_backend = next(iter(available))
        else:
            tool_backend = "claude"
    return tool_backend


async def _auto_title(chat_id: str, message: str):
    title = message if len(message) <= 80 else message[:77] + "..."
    await chat_store.rename_chat(chat_id, title)


@router.get("/chats", response_model=list[ChatResponse])
@limiter.limit("30/minute")
async def list_chats(request: Request, project_id: int = None):
    if project_id:
        return await chat_store.list_chats(project_id=project_id)
    return await chat_store.list_chats()


@router.post("/chats", response_model=ChatResponse)
@limiter.limit("10/minute")
async def create_chat(request: Request, body: ChatCreateRequest):
    backend = body.tool_backend or "claude"
    chat = await chat_store.create_chat(
        project_id=body.project_id,
        tool_backend=backend,
    )
    return chat


@router.get("/chats/{chat_id}", response_model=ChatResponse)
@limiter.limit("30/minute")
async def get_chat(request: Request, chat_id: str):
    chat = await chat_store.get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.patch("/chats/{chat_id}", response_model=ChatResponse)
@limiter.limit("10/minute")
async def update_chat(request: Request, chat_id: str, body: ChatUpdateRequest):
    if body.title is not None:
        ok = await chat_store.rename_chat(chat_id, body.title)
        if not ok:
            raise HTTPException(status_code=404, detail="Chat not found")
    chat = await chat_store.get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.delete("/chats/{chat_id}")
@limiter.limit("10/minute")
async def delete_chat(request: Request, chat_id: str):
    ok = await chat_store.delete_chat(chat_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"ok": True}


@router.get("/chats/{chat_id}/messages", response_model=list[MessageResponse])
@limiter.limit("30/minute")
async def get_messages(request: Request, chat_id: str):
    chat = await chat_store.get_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return await chat_store.list_messages(chat_id)


@router.post("/chat/send")
@limiter.limit("10/minute")
async def send_message(request: Request, body: ChatSendRequest):
    chat = await chat_store.get_chat(body.chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    tool_backend = await _get_backend_for_chat(chat)
    await chat_store.add_message(body.chat_id, "user", body.message)

    messages = await chat_store.list_messages(body.chat_id)
    user_msg_count = sum(1 for m in messages if m["role"] == "user")
    if user_msg_count == 1:
        await _auto_title(body.chat_id, body.message)

    backend = get_backend(tool_backend)
    if backend is None:
        raise HTTPException(status_code=400, detail=f"Backend '{tool_backend}' not available")

    cmd = backend.build_command(
        message=body.message,
        session_id=str(body.chat_id),
        first=user_msg_count <= 1,
    )

    job = runner.create_job(tool_backend, cmd, cwd=str(BASE_DIR))
    asyncio.create_task(runner.run_job(job))

    return StreamingResponse(runner.stream_logs(job), media_type="text/event-stream")


@router.post("/files/upload")
@limiter.limit("10/minute")
async def upload_file(request: Request, file: UploadFile = File(...)):
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB)")
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    file_path = UPLOADS_DIR / file.filename
    content = await file.read()
    file_path.write_bytes(content)
    return {"filename": file.filename, "size": len(content), "path": str(file_path)}
