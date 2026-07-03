# Agent-to-Agent Protocol

Defines the message types, handoff sequences, and escalation paths for autonomous agent communication in **Agentic Software Boutique**.

## Message Types

### HandoffRequest

Sent when an agent needs to pass work to another agent.

```json
{
  "type": "handoff_request",
  "from": "qa-tester",
  "to": "tech-lead",
  "session_id": "uuid",
  "payload": {
    "issue_id": 42,
    "reason": "loop_exhausted",
    "attempt_count": 3,
    "context_snapshot": "Summary of what was tried and what failed",
    "severity": "blocker"
  },
  "timestamp": "2026-07-02T12:00:00Z"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Always `handoff_request` |
| `from` | string | Agent role identifier |
| `to` | string | Target agent role identifier |
| `session_id` | string | Unique session identifier |
| `payload.reason` | string | Why the handoff is happening |
| `payload.attempt_count` | int | Number of retry attempts (for loops) |
| `payload.context_snapshot` | string | Summary of what was tried |
| `payload.severity` | string | `info`, `warning`, `blocker`, `critical` |

### HandoffResponse

Response to a HandoffRequest.

```json
{
  "type": "handoff_response",
  "from": "tech-lead",
  "to": "qa-tester",
  "session_id": "uuid",
  "payload": {
    "request_id": "uuid",
    "status": "accepted",
    "notes": "Will triage and delegate to Dev"
  },
  "timestamp": "2026-07-02T12:00:05Z"
}
```

| `payload.status` | Meaning |
|------------------|---------|
| `accepted` | Target agent takes ownership |
| `rejected` | Target agent cannot handle — sender must escalate |
| `redirected` | Target suggests a different recipient (in `notes`) |

### HandoffSequence

Standard handoff sequences by scenario.

**QA Loop Exhaustion (3 failures)**:
```
QA → [HandoffRequest(reason=loop_exhausted, to=tech-lead)]
  → Tech Lead → [HandoffRequest(reason=escalation_relay, to=cto)]
    → CTO + Advisory (plan mode)
    → CTO → [HandoffRequest(reason=plan_ready, to=tech-lead)]
      → Tech Lead adds technical context
      → Tech Lead → [HandoffRequest(reason=delegation, to=fullstack-developer)]
        → Dev implements → Tech Lead Code Review → CTO merge → QA re-validate
```

**Security Finding**:
```
Security Specialist → [creates Issue]
  → Tech Lead reads issue → [HandoffRequest(reason=triage_complete, to=fullstack-developer)]
    → Dev implements → Tech Lead Code Review → CTO merge → Security verifies
```

**UI/UX Finding**:
```
UI/UX Specialist → [creates Issue]
  → Tech Lead reads issue → [HandoffRequest(reason=triage_complete, to=fullstack-developer)]
    → Dev implements → Tech Lead Code Review → CTO merge → UI/UX verifies
```

## Escalation Levels

| Level | Trigger | Action |
|-------|---------|--------|
| `info` | Non-blocking observation | Document in issue comment |
| `warning` | Potential issue, needs attention | Create issue, Tech Lead triages |
| `blocker` | Blocks current work | HandoffRequest to next role in pipeline |
| `critical` | Security vuln, data loss risk | HandoffRequest to CTO directly (bypass Tech Lead) |

## Addressing

Agents are addressed by their role identifier (lowercase, hyphens):
- `cto`
- `tech-lead`
- `fullstack-developer`
- `qa-tester`
- `security-specialist`
- `ui-ux-specialist`
- `advisory`

## Context Propagation

When a subtask completes, its result is automatically available to dependent subtasks. The executor injects the result of completed dependencies into the context of each new subtask via `AgentContext.env`:

```
SUBTASK_A_RESULT=<json>
SUBTASK_B_RESULT=<json>
```

Dependent subtasks can read these environment variables to access prior results.

## Validation

Every HandoffRequest MUST include:
1. A valid `from` and `to` role identifier
2. A `reason` from the allowed set
3. A `context_snapshot` summarizing what led to the handoff
4. A `severity` level

Invalid or incomplete handoff messages are rejected with a `handoff_response(status=rejected, notes="missing required field")`.

See `specs/workflow.yaml` for the machine-readable workflow definition.
See `specs/workflow.md` for the pipeline in prose.
