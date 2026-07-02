import asyncio

from loguru import logger

from . import chat_store
from .approvals import create_approval, get_pending_for_task
from .hermes_adapter import get_kanban_path, is_available
from .kanban import list_tasks

POLL_INTERVAL_SECONDS = 5
INTERESTING_STATUSES = {"done", "blocked", "review", "running"}
STATUS_RANK = {"running": 1, "review": 2, "blocked": 3, "done": 4}
_seen: dict[tuple[str, str], str] = {}
_task = None


def _tenant_to_chat_id(tenant: str | None) -> str | None:
    if not tenant or not tenant.startswith("chat:"):
        return None
    return tenant[len("chat:"):]


def _should_notify(prev: str | None, current: str) -> bool:
    if current not in INTERESTING_STATUSES:
        return False
    if prev is None:
        return True
    if prev not in INTERESTING_STATUSES:
        return True
    return STATUS_RANK.get(current, 0) > STATUS_RANK.get(prev, 0)


async def _poll_once() -> None:
    if not is_available():
        return
    try:
        tasks = await list_tasks()
    except Exception as exc:
        logger.debug("Kanban poll failed: {}", exc)
        return

    for task_data in tasks:
        tenant = task_data.get("tenant")
        chat_id = _tenant_to_chat_id(tenant)
        if not chat_id:
            continue
        task_id = task_data.get("id")
        status = task_data.get("status")
        if not task_id or not status:
            continue
        key = (tenant or "", task_id)
        prev = _seen.get(key)
        if not _should_notify(prev, status):
            continue
        chat = await chat_store.get_chat(chat_id)
        if not chat:
            continue
        body = task_data.get("body") or ""
        summary = body.splitlines()[0][:120] if body else task_data.get("title", "")
        embed = (
            f"[kanban] Task {task_id} → {status}\n"
            f"Title: {task_data.get('title')}\n"
            f"Body: {summary}"
        )
        existing = await chat_store.list_messages(chat_id)
        if any(m["role"] == "system" and f"Task {task_id} → {status}" in (m.get("content") or "") for m in existing):
            _seen[key] = status
        else:
            try:
                await chat_store.add_message(chat_id, "system", embed)
                _seen[key] = status
                logger.info("Notified chat {} about kanban task {}", chat_id, task_id)
            except Exception as exc:
                logger.error("Failed to append kanban feedback to chat {}: {}", chat_id, exc)

        if status == "review":
            existing_approval = await get_pending_for_task(task_id)
            if existing_approval is None:
                await create_approval(
                    kanban_task_id=task_id,
                    kanban_tenant=tenant,
                    task_title=task_data.get("title"),
                )
                logger.info("Created approval pending for review task {}", task_id)


async def poll_once() -> None:
    await _poll_once()


async def _poll_loop() -> None:
    logger.info("Kanban→chat feedback loop started (db={})", get_kanban_path())
    while True:
        try:
            await _poll_once()
        except Exception as exc:
            logger.error("Kanban poll cycle error: {}", exc)
        await asyncio.sleep(POLL_INTERVAL_SECONDS)


def start() -> asyncio.Task | None:
    global _task
    if _task is not None and not _task.done():
        return _task
    _task = asyncio.create_task(_poll_loop())
    return _task


def stop() -> None:
    global _task
    if _task is not None:
        _task.cancel()
        _task = None
