---
name: agent-os-kanban
description: Agent OS kanban board for task tracking and delegation
version: 1.0.0
author: agent-os
metadata:
  hermes:
    tags: [platform, kanban, tasks, agent-os]
    requires_toolsets: [terminal, web]
---

## Description

The kanban board tracks tasks across the software development workflow. Tasks have titles, statuses, assignments, and comments. The orchestration system decomposes goals into kanban tasks and delegates them to agents.

## API

Base path: `/api/kanban`

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/kanban/tasks | List tasks (filter by `?tenant=`, `?status=`) |
| POST | /api/kanban/tasks | Create task (`title`, `tenant`) |
| PATCH | /api/kanban/tasks/{id} | Update task (`status`, `assignee`) |
| POST | /api/kanban/tasks/{id}/comments | Add comment |
| GET | /api/kanban/tasks/{id}/comments | Get comments |

## Statuses

- `todo` — task created, not started
- `in_progress` — actively being worked on
- `done` — completed
- `blocked` — waiting on something

## Workflow

1. Decompose a goal into tasks (one per logical step)
2. Create kanban tasks via POST
3. Assign tasks to agents (via Hermes delegate)
4. Track progress via GET /tasks with tenant filter
5. Close tasks via PATCH status=done

## Verification

Create a task, update its status, add a comment, and list tasks for the tenant.
