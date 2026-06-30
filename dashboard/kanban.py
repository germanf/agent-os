import json

from loguru import logger

from .hermes_adapter import get_kanban_path, is_available, run_command


def _shared_env() -> dict:
    return {"HERMES_KANBAN_DB": str(get_kanban_path())}


async def list_tasks(status: str | None = None, tenant: str | None = None) -> list[dict]:
    if not is_available():
        logger.warning("Hermes not available — cannot list kanban tasks")
        return []
    args = ["kanban", "list", "--json"]
    if status:
        args += ["--status", status]
    if tenant:
        args += ["--tenant", tenant]
    code, out, err = await run_command(args, env=_shared_env())
    if code != 0:
        logger.error("Failed to list kanban tasks: {} {}", out, err)
        return []
    try:
        return json.loads(out) if out.strip() else []
    except json.JSONDecodeError:
        logger.error("Failed to parse kanban list output: {}", out[:200])
        return []


async def create_task(
    title: str,
    body: str | None = None,
    assignee: str | None = None,
    priority: int | None = None,
    tenant: str | None = None,
) -> dict | None:
    if not is_available():
        logger.warning("Hermes not available — cannot create kanban task")
        return None
    args = ["kanban", "create", "--json", title]
    if body:
        args += ["--body", body]
    if assignee:
        args += ["--assignee", assignee]
    if priority is not None:
        args += ["--priority", str(priority)]
    if tenant:
        args += ["--tenant", tenant]
    code, out, err = await run_command(args, env=_shared_env())
    if code != 0:
        logger.error("Failed to create kanban task: {} {}", out, err)
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        logger.warning("Could not parse create output: {}", out[:200])
        return None


async def show_task(task_id: str) -> dict | None:
    if not is_available():
        return None
    code, out, err = await run_command(["kanban", "show", task_id], env=_shared_env())
    if code != 0:
        return None
    return {"id": task_id, "details": out}


async def complete_task(task_id: str) -> bool:
    if not is_available():
        return False
    code, out, err = await run_command(["kanban", "complete", task_id], env=_shared_env())
    return code == 0


async def block_task(task_id: str, reason: str) -> bool:
    if not is_available():
        return False
    code, out, err = await run_command(["kanban", "block", "--reason", reason, task_id], env=_shared_env())
    return code == 0


async def unblock_task(task_id: str) -> bool:
    if not is_available():
        return False
    code, out, err = await run_command(["kanban", "unblock", task_id], env=_shared_env())
    return code == 0
