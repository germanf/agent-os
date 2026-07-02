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
└── OrchestratorCapability — decompose(), delegate(), status()
```

### Implemented Agents

| Agent | Capability | File | Description |
|-------|-----------|------|-------------|
| `OpencodeAgent` | DeveloperCapability | `agents/opencode_agent.py` | Connects to OpenCode server, implements features, fixes bugs, refactors code |
| `HermesAgent` | OrchestratorCapability | `agents/hermes_agent.py` | Decomposes goals into kanban tasks, delegates to available agents, tracks progress |

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

## Orchestration

The orchestrator (`dashboard/orchestrator/`) manages multi-agent execution:

1. **Task Graph**: A DAG of subtasks with dependencies
2. **Agent Pool**: Registered agents with health status
3. **Executor**: Topological sort → parallel/sequential execution → retry on failure
4. **Aggregator**: Collates results with agent attribution

### Flow

```
Goal → TaskGraph (DAG) → Topological Sort → Agent Assignment → 
Parallel Execution → SSE Streaming → Result Aggregation → Report
```

## MCP Tool Access

Agents can discover and call tools via the MCP system:

- **4 MCP servers** registered on startup
- Tools for memory, notes, kanban, and workflow operations
- MCP tools are exposed to agents for self-service capabilities
