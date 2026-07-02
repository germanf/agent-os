# Agent System

## Overview

The agent system provides two layers: **agent capabilities** (what agents can do) and **chat backends** (how agents are invoked). This separation allows any capability to be paired with any backend.

## Agent Capabilities

Defined in `dashboard/agents/protocol.py`:

```
AgentCapability (ABC)
├── DeveloperCapability — fix_bug(), implement_feature(), refactor()
├── ReviewerCapability — review_pr(), check_standards()
├── QACapability — write_tests(), run_validation()
├── SecurityCapability — run_static_analysis(), run_dependency_audit(), create_finding_issue()
├── UIUXCapability — review_design(), audit_accessibility(), create_design_issue()
└── OrchestratorCapability — decompose(), delegate(), status()
```

### Agent Hierarchy

```
CTO ── launches agents, verifies workflows, approves PRs, sole PR-to-main authority
 ├── Tech Lead ── Code Review (mandatory gate), Security/UI-UX triage, delegate to Dev
 ├── Full Stack Developer ── implementation
 ├── QA/Tester ── validation, QA loop
 ├── Security Specialist ── pentesting, SAST/DAST → creates Issue
 └── UI/UX Specialist ── design/UX review, accessibility audit → creates Issue
      ↑
 Advisory ── deep architecture review on CTO request (loop exhaustion, complex design)
```

### Implemented Agents

| Agent | Capability | File | Description |
|-------|-----------|------|-------------|
| `OpencodeAgent` | DeveloperCapability | `agents/opencode_agent.py` | Connects to OpenCode server, implements features, fixes bugs, refactors code |
| `HermesAgent` | OrchestratorCapability | `agents/hermes_agent.py` | Decomposes goals into kanban tasks, delegates to available agents, tracks progress |
| `TechLeadAgent` | ReviewerCapability | `agents/reviewer.py` | Automated code review, PR validation, standards checking |
| `SecuritySpecialistAgent` | SecurityCapability | `agents/security_agent.py` | Static analysis, dependency auditing, vulnerability issue creation |
| `UIUXSpecialistAgent` | UIUXCapability | `agents/uiux_agent.py` | Design review, accessibility audit, UI consistency checks |

### Lifecycle

1. **Registration**: Agents register themselves on startup via `dashboard/agents/__init__.py`
2. **Discovery**: The agent pool (`dashboard/orchestrator/agent_pool.py`) profiles all registered agents
3. **Health checks**: Pool checks agent availability every 60 seconds
4. **Delegation**: The orchestrator assigns subtasks to available agents based on capability

## Chat Backends

Defined in `dashboard/backends/`:

| Backend | Status | Mechanism |
|---------|--------|-----------|
| `ClaudeBackend` | ✅ Complete | Subprocess: `claude -p` with `--output-format stream-json` |
| `OpencodeBackend` | ✅ Complete | HTTP API (OpenCode server) + subprocess fallback |
| `CodexBackend` | ⚠️ Stub | Not implemented |
| `KimiBackend` | ⚠️ Stub | Not implemented |

## Handoff Protocol

Agents communicate via structured handoff messages defined in `specs/protocol.md`:

- `HandoffRequest`: from → to, reason, severity, context_snapshot, attempt_count
- `HandoffResponse`: accepted, rejected, redirected
- Escalation levels: info → warning → blocker → critical

Standard handoff sequences:
- **QA loop exhaustion**: QA → Tech Lead → CTO + Advisory → plan → Tech Lead → Dev → re-QA
- **Security finding**: Security Specialist → Issue → Tech Lead → Dev → Review → Merge → Verify
- **UI/UX finding**: UI/UX Specialist → Issue → Tech Lead → Dev → Review → Merge → Verify

## Orchestration

The orchestrator (`dashboard/orchestrator/`) manages multi-agent execution:

1. **Task Graph**: A DAG of subtasks with dependencies
2. **Agent Pool**: Registered agents with health status
3. **Executor**: Topological sort → parallel/sequential execution → retry on failure → context propagation
4. **Aggregator**: Collates results with agent attribution

### Flow

```
Goal → TaskGraph (DAG) → Topological Sort → Agent Assignment →
Parallel Execution → SSE Streaming → Result Aggregation → Report
```

### Context Propagation

When a subtask completes, its result is automatically available to dependent subtasks via environment variables (`SUBTASK_{id}_RESULT`). This allows pipelines where the output of one agent feeds into the next.

## MCP Tool Access

Agents can discover and call tools via the MCP system:

- **4 MCP servers** registered on startup
- Tools for memory, notes, kanban, and workflow operations
- MCP tools are exposed to agents for self-service capabilities
