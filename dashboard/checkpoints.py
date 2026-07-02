import json
import time
from pathlib import Path

import aiosqlite

from .chat_store import DB_PATH


async def init_checkpoints(db_path: Path = DB_PATH) -> None:
    async with aiosqlite.connect(str(db_path)) as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS job_checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                tool TEXT NOT NULL,
                command_json TEXT NOT NULL,
                cwd TEXT NOT NULL,
                env_json TEXT,
                status TEXT NOT NULL,
                exit_code INTEGER,
                started_at REAL,
                ended_at REAL,
                logs_json TEXT,
                created_at REAL NOT NULL,
                resumed INTEGER DEFAULT 0,
                orphaned INTEGER DEFAULT 0
            )
            """
        )
        await conn.commit()


class CheckpointStore:
    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or DB_PATH

    async def save(
        self,
        job_id: str,
        tool: str,
        command: list[str],
        cwd: str,
        env: dict[str, str] | None,
        status: str,
        exit_code: int | None,
        started_at: float | None,
        ended_at: float | None,
        logs: list[str],
        orphaned: bool = False,
    ) -> dict:
        now = time.time()
        async with aiosqlite.connect(str(self.db_path)) as conn:
            conn.row_factory = aiosqlite.Row
            cur = await conn.execute(
                """INSERT INTO job_checkpoints
                   (job_id, tool, command_json, cwd, env_json, status, exit_code,
                    started_at, ended_at, logs_json, created_at, orphaned)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    job_id,
                    tool,
                    json.dumps(command),
                    cwd,
                    json.dumps(env) if env else None,
                    status,
                    exit_code,
                    started_at,
                    ended_at,
                    json.dumps(logs),
                    now,
                    1 if orphaned else 0,
                ),
            )
            await conn.commit()
            cp_id = cur.lastrowid
            cur2 = await conn.execute("SELECT * FROM job_checkpoints WHERE id=?", (cp_id,))
            row = await cur2.fetchone()
            return self._row_to_dict(row)

    async def list_orphans(self) -> list[dict]:
        async with aiosqlite.connect(str(self.db_path)) as conn:
            conn.row_factory = aiosqlite.Row
            cur = await conn.execute(
                "SELECT * FROM job_checkpoints WHERE orphaned=1 AND resumed=0 ORDER BY created_at DESC"
            )
            rows = await cur.fetchall()
            return [self._row_to_dict(r) for r in rows]

    async def list_resumable(self, status_prefix: str | None = None) -> list[dict]:
        async with aiosqlite.connect(str(self.db_path)) as conn:
            conn.row_factory = aiosqlite.Row
            if status_prefix:
                cur = await conn.execute(
                    "SELECT * FROM job_checkpoints WHERE resumed=0 AND status LIKE ? ORDER BY created_at DESC",
                    (f"{status_prefix}%",),
                )
            else:
                cur = await conn.execute(
                    "SELECT * FROM job_checkpoints WHERE resumed=0 ORDER BY created_at DESC"
                )
            rows = await cur.fetchall()
            return [self._row_to_dict(r) for r in rows]

    async def get(self, cp_id: int) -> dict | None:
        async with aiosqlite.connect(str(self.db_path)) as conn:
            conn.row_factory = aiosqlite.Row
            cur = await conn.execute("SELECT * FROM job_checkpoints WHERE id=?", (cp_id,))
            row = await cur.fetchone()
            return self._row_to_dict(row)

    async def mark_resumed(self, cp_id: int) -> None:
        async with aiosqlite.connect(str(self.db_path)) as conn:
            await conn.execute(
                "UPDATE job_checkpoints SET resumed=1 WHERE id=?", (cp_id,)
            )
            await conn.commit()

    async def mark_orphans(self) -> int:
        async with aiosqlite.connect(str(self.db_path)) as conn:
            cur = await conn.execute(
                """UPDATE job_checkpoints
                      SET orphaned=1
                    WHERE status IN ('running', 'queued')
                      AND orphaned=0"""
            )
            await conn.commit()
            return cur.rowcount

    @staticmethod
    def _row_to_dict(row: aiosqlite.Row | None) -> dict | None:
        if row is None:
            return None
        d = dict(row)
        d["command"] = json.loads(d.pop("command_json") or "[]")
        d["env"] = json.loads(d.pop("env_json")) if d.get("env_json") else None
        d["logs"] = json.loads(d.pop("logs_json") or "[]")
        return d
