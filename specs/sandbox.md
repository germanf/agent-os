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

## Implementation

This project's sandbox implementation lives in `sandbox/`.
See `sandbox/README.md` for detailed setup, scripts, and troubleshooting.
See `sandbox/VALIDATION.md` for test documentation.

## Agent roles

See `specs/roles/` for role definitions and responsibilities.
