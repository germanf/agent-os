---
name: agent-os-workflows
description: Agent OS workflow engine for multi-step task execution
version: 1.0.0
author: agent-os
metadata:
  hermes:
    tags: [platform, workflows, orchestration, agent-os]
    requires_toolsets: [terminal, web]
---

## Description

The workflow engine executes multi-step tasks defined as WorkflowDef objects. Each workflow consists of ordered steps that run sequentially. Steps can run shell commands, call APIs, or invoke agent capabilities.

## Workflow Definition

A workflow has:
- `name` — unique identifier
- `steps` — ordered list of WorkflowStep
- `context` — shared env vars across steps

Each step has:
- `id` — step identifier
- `command` — shell command to execute
- `cwd` — working directory (optional)
- `timeout` — max execution time (optional)

## API

Base path: `/api/workflows`

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/workflows | Create a workflow definition |
| POST | /api/workflows/{id}/execute | Execute a workflow |
| GET | /api/workflows/{id}/status | Get execution status |
| GET | /api/workflows | List workflow definitions |

## Workflow Execution

```
POST /api/workflows/1/execute
```

Returns a job ID. Poll status via:
```
GET /api/workflows/1/status?job_id=<id>
```

## When to Use

- Automate multi-step processes (deploy, test, build)
- Enforce sequential ordering of dependent tasks
- Combine with kanban for manual + automated mixed workflows

## Verification

Create a workflow with echo steps, execute it, and verify the output.
