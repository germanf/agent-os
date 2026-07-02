---
name: agent-os-memory
description: Agent OS memory system — project and org memory APIs
version: 1.0.0
author: agent-os
metadata:
  hermes:
    tags: [platform, memory, agent-os]
    requires_toolsets: [terminal, web]
---

## Description

Agent OS provides two memory layers for persistent agent state: Project Memory (per-project key-value) and Org Memory (cross-project knowledge base). Both are backed by SQLite.

## Project Memory API

Base path: `/api/projects/{project_id}/memory`

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/projects/{id}/memory | List all keys for a project |
| POST | /api/projects/{id}/memory | Set key-value (`key`, `value` in JSON body) |
| GET | /api/projects/{id}/memory/{key} | Get specific key |
| DELETE | /api/projects/{id}/memory/{key} | Delete key |

Example:
```
POST /api/projects/1/memory
{"key": "last_branch", "value": "feature/foo"}
```

## Org Memory API

Base path: `/api/memory/org`

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/memory/org | List (optional `?tag=`) |
| POST | /api/memory/org | Store with `key`, `value`, `tags`, `source_project_id` |
| GET | /api/memory/org/search?q= | Full-text search |
| GET | /api/memory/org/{key} | Get specific key |
| DELETE | /api/memory/org/{key} | Delete key |

## When to Use

- Use Project Memory to persist per-project state: current branch, decisions, blockers, next steps
- Use Org Memory to share knowledge across projects: discovered patterns, conventions, reusable solutions
- Memory survives agent restarts and is shared across agents

## Verification

Save a memory, retrieve it, then delete it using the API.
