---
name: agent-os-token-accounting
description: Log and query token usage via the token accounting API
version: 1.0.0
author: agent-os
metadata:
  hermes:
    tags: [platform, tokens, monitoring, agent-os]
    requires_toolsets: [terminal, web]
---

## Description

Track token consumption per session, project, and agent via the token accounting system. The API provides logging, listing, and aggregated summaries.

## API

Base path: `/api/tokens`

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/tokens | List usage (filter by `?project_id=`, `?session_id=`, `?limit=`) |
| POST | /api/tokens | Log a token usage entry |
| GET | /api/tokens/summary | Aggregated totals by project/agent/model |

## Logging Usage

```
POST /api/tokens
{
  "session_id": "session-abc",
  "project_id": 1,
  "prompt_tokens": 500,
  "completion_tokens": 200,
  "agent_name": "hermes",
  "model": "claude-sonnet-4"
}
```

## Querying Summary

```
GET /api/tokens/summary?project_id=1
```

Returns sums grouped by project, agent_name, and model.

## When to Use

- Log token usage after each agent interaction
- Query summary before reporting costs to the user
- Track token consumption per project to identify expensive operations

## Verification

Log a usage entry, then list it and check the summary endpoint.
