from __future__ import annotations

import time
from pathlib import Path

import aiosqlite

from .chat_store import DB_PATH


async def init_memory(db_path: Path = DB_PATH) -> None:
    async with aiosqlite.connect(str(db_path)) as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS project_memory (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                key        TEXT NOT NULL,
                value      TEXT NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                UNIQUE(project_id, key)
            )
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS org_memory (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                source_project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
                key               TEXT NOT NULL UNIQUE,
                value             TEXT NOT NULL,
                tags              TEXT DEFAULT '',
                created_at        REAL NOT NULL
            )
            """
        )
        await conn.commit()


class ProjectMemoryStore:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path

    async def set(self, project_id: int, key: str, value: str) -> dict:
        now = time.time()
        async with aiosqlite.connect(str(self.db_path)) as conn:
            conn.row_factory = aiosqlite.Row
            await conn.execute(
                """INSERT INTO project_memory (project_id, key, value, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(project_id, key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at""",
                (project_id, key, value, now, now),
            )
            await conn.commit()
            cur = await conn.execute(
                "SELECT * FROM project_memory WHERE project_id=? AND key=?",
                (project_id, key),
            )
            row = await cur.fetchone()
            return dict(row) if row else {"project_id": project_id, "key": key, "value": value}

    async def get(self, project_id: int, key: str) -> dict | None:
        async with aiosqlite.connect(str(self.db_path)) as conn:
            conn.row_factory = aiosqlite.Row
            cur = await conn.execute(
                "SELECT * FROM project_memory WHERE project_id=? AND key=?",
                (project_id, key),
            )
            row = await cur.fetchone()
            return dict(row) if row else None

    async def list(self, project_id: int) -> list[dict]:
        async with aiosqlite.connect(str(self.db_path)) as conn:
            conn.row_factory = aiosqlite.Row
            cur = await conn.execute(
                "SELECT * FROM project_memory WHERE project_id=? ORDER BY key",
                (project_id,),
            )
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def delete(self, project_id: int, key: str) -> bool:
        async with aiosqlite.connect(str(self.db_path)) as conn:
            cur = await conn.execute(
                "DELETE FROM project_memory WHERE project_id=? AND key=?",
                (project_id, key),
            )
            await conn.commit()
            return cur.rowcount > 0


class OrgMemoryStore:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path

    async def set(self, key: str, value: str, source_project_id: int | None = None, tags: str = "") -> dict:
        now = time.time()
        async with aiosqlite.connect(str(self.db_path)) as conn:
            conn.row_factory = aiosqlite.Row
            await conn.execute(
                """INSERT INTO org_memory (source_project_id, key, value, tags, created_at)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(key) DO UPDATE SET value=excluded.value, tags=excluded.tags""",
                (source_project_id, key, value, tags, now),
            )
            await conn.commit()
            cur = await conn.execute("SELECT * FROM org_memory WHERE key=?", (key,))
            row = await cur.fetchone()
            return dict(row) if row else {"key": key, "value": value}

    async def get(self, key: str) -> dict | None:
        async with aiosqlite.connect(str(self.db_path)) as conn:
            conn.row_factory = aiosqlite.Row
            cur = await conn.execute("SELECT * FROM org_memory WHERE key=?", (key,))
            row = await cur.fetchone()
            return dict(row) if row else None

    async def search(self, query: str) -> list[dict]:
        async with aiosqlite.connect(str(self.db_path)) as conn:
            conn.row_factory = aiosqlite.Row
            pattern = f"%{query}%"
            cur = await conn.execute(
                """SELECT * FROM org_memory
                   WHERE key LIKE ? OR value LIKE ? OR tags LIKE ?
                   ORDER BY created_at DESC""",
                (pattern, pattern, pattern),
            )
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def list_all(self, tag: str | None = None) -> list[dict]:
        async with aiosqlite.connect(str(self.db_path)) as conn:
            conn.row_factory = aiosqlite.Row
            if tag:
                cur = await conn.execute(
                    "SELECT * FROM org_memory WHERE tags LIKE ? ORDER BY created_at DESC",
                    (f"%{tag}%",),
                )
            else:
                cur = await conn.execute("SELECT * FROM org_memory ORDER BY created_at DESC")
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def delete(self, key: str) -> bool:
        async with aiosqlite.connect(str(self.db_path)) as conn:
            cur = await conn.execute("DELETE FROM org_memory WHERE key=?", (key,))
            await conn.commit()
            return cur.rowcount > 0
