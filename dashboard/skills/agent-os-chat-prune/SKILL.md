---
name: agent-os-chat-prune
description: Chat message pruning — deletes messages older than 7 days
version: 1.0.0
author: agent-os
metadata:
  hermes:
    tags: [workflow, operational, chat_prune]
    requires_toolsets: [terminal]
---

## Description

Chat message pruning — deletes messages older than 7 days.

## Last Run

- Timestamp: 2026-07-03 19:24:24 UTC
- Status: completed
- Result: {'pruned_messages': 10}

## How to Invoke

This workflow runs on a cron schedule managed by the internal scheduler.
To trigger manually:

```bash
curl -X POST $BASE_URL/api/scheduler/run -d '{"workflow": "chat_prune"}'
```
