# Database Schema

**DB:** SQLite at `dashboard/data/chat.db` (WAL mode)
**Managed by:** `dashboard/chat_store.py`
**Created:** Auto on `@app.on_event("startup")` via `chat_store.init_db()`

## Tables

### `projects`

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | Auto-increment |
| `name` | TEXT | NOT NULL |
| `system_prompt` | TEXT | Nullable, appended to Claude calls |
| `created_at` | REAL | Unix timestamp |

### `project_folders`

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | Auto-increment |
| `project_id` | INTEGER | FK → `projects(id)` ON DELETE CASCADE |
| `path` | TEXT | NOT NULL, filesystem path |
| `created_at` | REAL | Unix timestamp |

### `chats`

| Column | Type | Notes |
|--------|------|-------|
| `id` | TEXT PK | UUID (dashed format, used as Claude session) |
| `project_id` | INTEGER | FK → `projects(id)` ON DELETE SET NULL |
| `title` | TEXT | Auto-generated from first response |
| `claude_session_id` | TEXT | Matches chat `id` by default |
| `created_at` | REAL | Unix timestamp |
| `updated_at` | REAL | Unix timestamp |

### `messages`

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | Auto-increment |
| `chat_id` | TEXT | FK → `chats(id)` ON DELETE CASCADE |
| `role` | TEXT | `"user"` or `"assistant"` |
| `content` | TEXT | Message text |
| `tool_calls` | TEXT | JSON blob (nullable), list of `{id, name, input, result}` |
| `created_at` | REAL | Unix timestamp |

## Indexes

| Name | Columns |
|------|---------|
| `idx_chats_project` | `chats(project_id)` |
| `idx_messages_chat` | `messages(chat_id)` |

## Constraints

- `PRAGMA foreign_keys = ON` (enforced per connection)
- `PRAGMA journal_mode = WAL` (concurrent reads)
