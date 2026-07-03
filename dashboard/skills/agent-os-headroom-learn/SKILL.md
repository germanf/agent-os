---
name: agent-os-headroom-learn
description: Headroom learn — runs scheduled failure mining on the codebase
version: 1.0.0
author: agent-os
metadata:
  hermes:
    tags: [workflow, operational, headroom_learn]
    requires_toolsets: [terminal]
---

## Description

Headroom learn — runs scheduled failure mining on the codebase.

## Last Run

- Timestamp: 2026-07-03 19:24:24 UTC
- Status: completed
- Result: {'status': 'ok'}

## How to Invoke

This workflow runs on a cron schedule managed by the internal scheduler.
To trigger manually:

```bash
curl -X POST $BASE_URL/api/scheduler/run -d '{"workflow": "headroom_learn"}'
```
