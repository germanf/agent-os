"""SQLite persistence for the /chat feature: projects, chats, and messages.

This is bookkeeping for the dashboard UI only (titles, sidebar listing,
project grouping) — it does not replace the claude CLI's own conversation
state, which is still kept via --session-id/--resume against its own
transcript under ~/.claude/projects/.
"""

from __future__ import annotations

import json
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import aiosqlite

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "chat.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    system_prompt TEXT,
    created_at    REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS project_folders (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    path        TEXT NOT NULL,
    created_at  REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS chats (
    id                 TEXT PRIMARY KEY,
    project_id         INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    title              TEXT NOT NULL DEFAULT '',
    claude_session_id  TEXT NOT NULL,
    tool_session_id    TEXT,
    tool_backend       TEXT NOT NULL DEFAULT 'claude',
    created_at         REAL NOT NULL,
    updated_at         REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id     TEXT NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    role        TEXT NOT NULL,
    content     TEXT NOT NULL,
    tool_calls  TEXT,
    created_at  REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_chats_project ON chats(project_id);
CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id);
"""


@asynccontextmanager
async def _connect(db_path: Path = DB_PATH):
    """Open a connection that commits on success, rolls back on error, and closes either way."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(db_path)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA foreign_keys = ON")
    await conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        await conn.commit()
    except Exception:
        await conn.rollback()
        raise
    finally:
        await conn.close()


async def init_db(db_path: Path = DB_PATH) -> None:
    async with _connect(db_path) as conn:
        await conn.executescript(_SCHEMA)
        # Migrations for existing databases
        for col, col_def in [
            ("tool_backend", "tool_backend TEXT NOT NULL DEFAULT 'claude'"),
            ("tool_session_id", "tool_session_id TEXT"),
        ]:
            try:
                await conn.execute(f"ALTER TABLE chats ADD COLUMN {col_def}")
            except Exception:
                pass  # Column already exists


# ── Projects ──────────────────────────────────────────────────────────────────

async def create_project(name: str, system_prompt: str | None = None, db_path: Path = DB_PATH) -> dict:
    now = time.time()
    async with _connect(db_path) as conn:
        cur = await conn.execute(
            "INSERT INTO projects (name, system_prompt, created_at) VALUES (?, ?, ?)",
            (name, system_prompt, now),
        )
        new_id = cur.lastrowid
    return await get_project(new_id, db_path=db_path)


async def list_projects(db_path: Path = DB_PATH) -> list[dict]:
    async with _connect(db_path) as conn:
        cur = await conn.execute("SELECT * FROM projects ORDER BY created_at DESC")
        rows = await cur.fetchall()
        return [await _project_dict(conn, row) for row in rows]


async def get_project(project_id: int, db_path: Path = DB_PATH) -> dict | None:
    async with _connect(db_path) as conn:
        cur = await conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = await cur.fetchone()
        return await _project_dict(conn, row) if row else None


async def update_project(
    project_id: int, name: str | None = None, system_prompt: str | None = None, db_path: Path = DB_PATH
) -> dict | None:
    fields, values = [], []
    if name is not None:
        fields.append("name = ?")
        values.append(name)
    if system_prompt is not None:
        fields.append("system_prompt = ?")
        values.append(system_prompt)
    if fields:
        async with _connect(db_path) as conn:
            await conn.execute(f"UPDATE projects SET {', '.join(fields)} WHERE id = ?", (*values, project_id))
    return await get_project(project_id, db_path=db_path)


async def delete_project(project_id: int, db_path: Path = DB_PATH) -> bool:
    async with _connect(db_path) as conn:
        cur = await conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        return cur.rowcount > 0


async def add_project_folder(project_id: int, path: str, db_path: Path = DB_PATH) -> dict:
    now = time.time()
    async with _connect(db_path) as conn:
        cur = await conn.execute(
            "INSERT INTO project_folders (project_id, path, created_at) VALUES (?, ?, ?)",
            (project_id, path, now),
        )
        folder_cur = await conn.execute("SELECT * FROM project_folders WHERE id = ?", (cur.lastrowid,))
        row = await folder_cur.fetchone()
        return dict(row)


async def remove_project_folder(folder_id: int, db_path: Path = DB_PATH) -> bool:
    async with _connect(db_path) as conn:
        cur = await conn.execute("DELETE FROM project_folders WHERE id = ?", (folder_id,))
        return cur.rowcount > 0


async def list_project_folders(project_id: int, db_path: Path = DB_PATH) -> list[dict]:
    async with _connect(db_path) as conn:
        cur = await conn.execute(
            "SELECT * FROM project_folders WHERE project_id = ? ORDER BY created_at", (project_id,)
        )
        rows = await cur.fetchall()
        return [dict(row) for row in rows]


async def _project_dict(conn: aiosqlite.Connection, row: aiosqlite.Row) -> dict:
    data = dict(row)
    folders_cur = await conn.execute(
        "SELECT * FROM project_folders WHERE project_id = ? ORDER BY created_at", (data["id"],)
    )
    folders = await folders_cur.fetchall()
    data["folders"] = [dict(f) for f in folders]
    return data


# ── Chats ─────────────────────────────────────────────────────────────────────

async def create_chat(
    chat_id: str | None = None,
    claude_session_id: str | None = None,
    project_id: int | None = None,
    tool_backend: str | None = None,
    db_path: Path = DB_PATH,
) -> dict:
    chat_id = chat_id or str(uuid.uuid4())
    claude_session_id = claude_session_id or chat_id
    tool_session_id: str = claude_session_id
    backend = tool_backend or "claude"
    now = time.time()
    async with _connect(db_path) as conn:
        await conn.execute(
            """INSERT INTO chats
               (id, project_id, title, claude_session_id, tool_session_id, tool_backend, created_at, updated_at)
               VALUES (?, ?, '', ?, ?, ?, ?, ?)""",
            (chat_id, project_id, claude_session_id, tool_session_id, backend, now, now),
        )
    return await get_chat(chat_id, db_path=db_path)


async def list_chats(project_id: int | None = None, db_path: Path = DB_PATH) -> list[dict]:
    async with _connect(db_path) as conn:
        if project_id is None:
            cur = await conn.execute("""
                SELECT c.* FROM chats c
                WHERE EXISTS (SELECT 1 FROM messages m WHERE m.chat_id = c.id)
                ORDER BY c.updated_at DESC
            """)
        else:
            cur = await conn.execute("""
                SELECT c.* FROM chats c
                WHERE c.project_id = ? AND EXISTS (SELECT 1 FROM messages m WHERE m.chat_id = c.id)
                ORDER BY c.updated_at DESC
            """, (project_id,))
        rows = await cur.fetchall()
        return [dict(row) for row in rows]


async def get_chat(chat_id: str, db_path: Path = DB_PATH) -> dict | None:
    async with _connect(db_path) as conn:
        cur = await conn.execute("SELECT * FROM chats WHERE id = ?", (chat_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def rename_chat(chat_id: str, title: str, db_path: Path = DB_PATH) -> bool:
    async with _connect(db_path) as conn:
        cur = await conn.execute("UPDATE chats SET title = ? WHERE id = ?", (title, chat_id))
        return cur.rowcount > 0


async def delete_chat(chat_id: str, db_path: Path = DB_PATH) -> bool:
    async with _connect(db_path) as conn:
        cur = await conn.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
        return cur.rowcount > 0


async def touch_chat(chat_id: str, db_path: Path = DB_PATH) -> None:
    async with _connect(db_path) as conn:
        await conn.execute("UPDATE chats SET updated_at = ? WHERE id = ?", (time.time(), chat_id))


# ── Messages ──────────────────────────────────────────────────────────────────

async def add_message(
    chat_id: str, role: str, content: str, tool_calls: list[dict] | None = None, db_path: Path = DB_PATH
) -> dict:
    now = time.time()
    payload = json.dumps(tool_calls) if tool_calls else None
    async with _connect(db_path) as conn:
        cur = await conn.execute(
            "INSERT INTO messages (chat_id, role, content, tool_calls, created_at) VALUES (?, ?, ?, ?, ?)",
            (chat_id, role, content, payload, now),
        )
        msg_cur = await conn.execute("SELECT * FROM messages WHERE id = ?", (cur.lastrowid,))
        row = await msg_cur.fetchone()
        return _message_dict(row)


async def list_messages(chat_id: str, db_path: Path = DB_PATH) -> list[dict]:
    async with _connect(db_path) as conn:
        cur = await conn.execute(
            "SELECT * FROM messages WHERE chat_id = ? ORDER BY id", (chat_id,)
        )
        rows = await cur.fetchall()
        return [_message_dict(row) for row in rows]


def _message_dict(row: aiosqlite.Row) -> dict:
    data = dict(row)
    data["tool_calls"] = json.loads(data["tool_calls"]) if data["tool_calls"] else None
    return data
