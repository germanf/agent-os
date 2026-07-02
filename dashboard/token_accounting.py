from __future__ import annotations

import time
from pathlib import Path

import aiosqlite

from .chat_store import DB_PATH


async def init_token_accounting(db_path: Path = DB_PATH) -> None:
    async with aiosqlite.connect(str(db_path)) as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS token_usage (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id        TEXT NOT NULL,
                project_id        INTEGER REFERENCES projects(id) ON DELETE SET NULL,
                agent_name        TEXT NOT NULL DEFAULT 'unknown',
                prompt_tokens     INTEGER NOT NULL DEFAULT 0,
                completion_tokens INTEGER NOT NULL DEFAULT 0,
                total_tokens      INTEGER NOT NULL DEFAULT 0,
                model             TEXT NOT NULL DEFAULT 'unknown',
                created_at        REAL NOT NULL
            )
            """
        )
        await conn.commit()


class TokenAccountant:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path

    async def log_usage(
        self,
        session_id: str,
        prompt_tokens: int,
        completion_tokens: int,
        project_id: int | None = None,
        agent_name: str = "unknown",
        model: str = "unknown",
    ) -> dict:
        now = time.time()
        total = prompt_tokens + completion_tokens
        async with aiosqlite.connect(str(self.db_path)) as conn:
            conn.row_factory = aiosqlite.Row
            cur = await conn.execute(
                """INSERT INTO token_usage
                    (session_id, project_id, agent_name, prompt_tokens,
                     completion_tokens, total_tokens, model, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (session_id, project_id, agent_name, prompt_tokens, completion_tokens, total, model, now),
            )
            await conn.commit()
            new_id = cur.lastrowid
            cur2 = await conn.execute("SELECT * FROM token_usage WHERE id=?", (new_id,))
            row = await cur2.fetchone()
            return dict(row) if row else {}

    async def list(
        self,
        project_id: int | None = None,
        session_id: str | None = None,
        from_ts: float | None = None,
        to_ts: float | None = None,
        limit: int = 100,
    ) -> list[dict]:
        conditions = []
        params: list = []
        if project_id is not None:
            conditions.append("project_id=?")
            params.append(project_id)
        if session_id:
            conditions.append("session_id=?")
            params.append(session_id)
        if from_ts is not None:
            conditions.append("created_at>=?")
            params.append(from_ts)
        if to_ts is not None:
            conditions.append("created_at<?")
            params.append(to_ts)
        where = "WHERE " + " AND ".join(conditions) if conditions else ""
        async with aiosqlite.connect(str(self.db_path)) as conn:
            conn.row_factory = aiosqlite.Row
            cur = await conn.execute(
                f"SELECT * FROM token_usage {where} ORDER BY created_at DESC LIMIT ?",
                (*params, limit),
            )
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def summary(self, project_id: int | None = None) -> list[dict]:
        where = "WHERE project_id=?" if project_id else ""
        params: list = [project_id] if project_id else []
        async with aiosqlite.connect(str(self.db_path)) as conn:
            conn.row_factory = aiosqlite.Row
            cur = await conn.execute(
                f"""SELECT project_id, agent_name, model,
                           SUM(prompt_tokens) as total_prompt,
                           SUM(completion_tokens) as total_completion,
                           SUM(total_tokens) as grand_total,
                           COUNT(*) as call_count
                    FROM token_usage {where}
                    GROUP BY project_id, agent_name, model
                    ORDER BY grand_total DESC""",
                params,
            )
            rows = await cur.fetchall()
            return [dict(r) for r in rows]
