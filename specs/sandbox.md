# Sandbox Isolation Conventions

Two isolation mechanisms for running parallel agents.

## 1. Git Worktree per Agent

Each agent works in its own `git worktree` (separate branch, separate directory).
This prevents branch conflicts when multiple agents work simultaneously.

## 2. Docker Containers per Role

Agents run in isolated Docker containers with role-based port ranges:

| Role | Port Range | Container Name Pattern |
|------|-----------|----------------------|
| Full Stack Developer | 8800–8849 | `sandbox-<agent-id>` |
| QA / Tester | 8850–8899 | `sandbox-<agent-id>` |
| UX/UI Designer | 8900–8949 | `sandbox-<agent-id>` |

### Rules

- Credentials inside the sandbox are always mocked (see `sandbox/fixtures/`).
- Cleanup order: stop container FIRST, then remove worktree.
- Single-agent projects may only need worktree isolation.

## 3. Project `tmp/` Directory

A gitignored `tmp/` directory at project root holds ephemeral runtime data:
test outputs, logs, generated artifacts that do not need to persist.

**Never** put shared or reusable data in `tmp/`. Specifically:

| Data | Location | Reason |
|------|----------|--------|
| Docker compose files | `sandbox/` | Used across roles, must be findable by name |
| Scripts | `sandbox/scripts/` | Versioned, shared by all agents |
| Fixtures | `sandbox/fixtures/` | Versioned, referenced by multiple scripts |
| **Ephemeral** (logs, test output) | `tmp/` | Not versioned, disposable per session |

## 4. Cleanup Lifecycle

The sandbox lifecycle follows:

```
sandbox-up.sh  →  sandbox-test.sh  →  [PR merged to dev]  →  sandbox-cleanup.sh
```

### Stages

1. **sandbox-up.sh** — Builds Docker image, picks port, generates compose file
   in `sandbox/`, starts container, runs CI checks.
2. **sandbox-test.sh** — Runs full test suite (startup, CI, endpoints, volumes,
   port range, cleanup).
3. **PR merged to dev** — After human approval and CTO merge of the feature PR.
4. **sandbox-cleanup.sh** — Verifies PR merge status via `gh pr view`, then tears
   down container, volumes, and removes compose file from `sandbox/`.

### Usage

```bash
# Full lifecycle with PR-gated cleanup
sandbox-up.sh qa agent-001 && \
sandbox-test.sh qa agent-001 && \
sandbox-cleanup.sh agent-001 54
```

## Implementation

This project's sandbox implementation lives in `sandbox/`.
See `sandbox/README.md` for detailed setup, scripts, and troubleshooting.
See `sandbox/VALIDATION.md` for test documentation.

## Agent roles

See `specs/roles/` for role definitions and responsibilities.
