import time
from pathlib import Path

import aiosqlite

from .chat_store import DB_PATH


async def init_approvals(db_path: Path = DB_PATH) -> None:
    async with aiosqlite.connect(str(db_path)) as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS approvals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kanban_task_id TEXT NOT NULL,
                kanban_tenant TEXT,
                task_title TEXT,
                status TEXT NOT NULL,
                created_at REAL NOT NULL,
                decided_at REAL,
                decided_by TEXT,
                decision TEXT
            )
            """
        )
        await conn.commit()


def _to_dict(row: aiosqlite.Row | None) -> dict | None:
    return dict(row) if row else None


async def create_approval(
    kanban_task_id: str,
    kanban_tenant: str | None = None,
    task_title: str | None = None,
    db_path: Path = DB_PATH,
) -> dict | None:
    now = time.time()
    async with aiosqlite.connect(str(db_path)) as conn:
        conn.row_factory = aiosqlite.Row
        existing = await conn.execute(
            "SELECT * FROM approvals WHERE kanban_task_id=? AND status='pending'",
            (kanban_task_id,),
        )
        existing_row = await existing.fetchone()
        if existing_row is not None:
            return dict(existing_row)
        cur = await conn.execute(
            """INSERT INTO approvals
               (kanban_task_id, kanban_tenant, task_title, status, created_at)
               VALUES (?, ?, ?, 'pending', ?)""",
            (kanban_task_id, kanban_tenant, task_title, now),
        )
        await conn.commit()
        new_id = cur.lastrowid
        cur2 = await conn.execute("SELECT * FROM approvals WHERE id=?", (new_id,))
        row = await cur2.fetchone()
        return _to_dict(row)


async def list_pending(db_path: Path = DB_PATH) -> list[dict]:
    async with aiosqlite.connect(str(db_path)) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute(
            "SELECT * FROM approvals WHERE status='pending' ORDER BY created_at DESC"
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_approval(approval_id: int, db_path: Path = DB_PATH) -> dict | None:
    async with aiosqlite.connect(str(db_path)) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute("SELECT * FROM approvals WHERE id=?", (approval_id,))
        row = await cur.fetchone()
        return _to_dict(row)


async def decide(
    approval_id: int,
    decision: str,
    decided_by: str = "user",
    db_path: Path = DB_PATH,
) -> dict | None:
    if decision not in ("approved", "denied"):
        return None
    now = time.time()
    async with aiosqlite.connect(str(db_path)) as conn:
        conn.row_factory = aiosqlite.Row
        await conn.execute(
            """
            UPDATE approvals
               SET status='decided', decided_at=?, decided_by=?, decision=?
             WHERE id=? AND status='pending'
            """,
            (now, decided_by, decision, approval_id),
        )
        await conn.commit()
        cur = await conn.execute("SELECT * FROM approvals WHERE id=?", (approval_id,))
        row = await cur.fetchone()
        return _to_dict(row)


async def get_pending_for_task(
    kanban_task_id: str, db_path: Path = DB_PATH
) -> dict | None:
    async with aiosqlite.connect(str(db_path)) as conn:
        conn.row_factory = aiosqlite.Row
        cur = await conn.execute(
            "SELECT * FROM approvals WHERE kanban_task_id=? AND status='pending'",
            (kanban_task_id,),
        )
        row = await cur.fetchone()
        return _to_dict(row)
