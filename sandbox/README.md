# Docker Sandboxes for Agent Execution (Phase 1)

## Purpose

This directory contains Docker sandbox infrastructure for running agents (fullstack, QA, UI) in isolated containers. Phase 1 provides the foundational setup: containerization, port management, and CI validation.

## Overview

Each agent runs in its own Docker container with:
- **Isolation**: Independent environment per agent role
- **Volume management**: Isolated `.venv` and `node_modules` per agent
- **Port allocation**: Role-based port ranges to prevent conflicts
- **CI validation**: Automated checks on startup (TypeScript, Python syntax)
- **Logging**: Structured JSON logs with agent metadata

## Architecture

### Directory Structure

```
sandbox/
├── Dockerfile.base              # Base image: Python 3.11 + Node.js 20
├── docker-compose.sandbox.yml   # Template for container config (parametrized)
├── .gitignore                   # Git ignore patterns
├── README.md                    # This file
│
├── scripts/                     # Management scripts
│   ├── pick-port.sh            # Find available port in role range
│   ├── sandbox-up.sh           # Start container + CI checks
│   ├── sandbox-down.sh         # Stop container + cleanup
│   ├── sandbox-cleanup.sh      # Post-PR-merge cleanup (PR-gated)
│   ├── sandbox-cleanup-all.sh  # Global cleanup of all sandboxes
│   ├── sandbox-test.sh         # Single agent validation
│   ├── parallel-test.sh        # Multi-agent parallel validation
│   ├── ci-checks.sh            # Validation checks (TypeScript, Python)
│   └── entrypoint.sh           # uvicorn startup script
│
└── fixtures/                    # Mock data for sandbox
    ├── credentials.dashboard.mock.json
    ├── env.dashboard.mock
    └── ~~env.agentic-twitter-claude.mock~~ (removed)

tmp/                              # Runtime artifacts (gitignored)
└── .docker-compose.<agent>.yml  # Generated compose files
```

### Port Ranges by Role

Agents are assigned ports from role-specific ranges to prevent conflicts:

| Role | Port Range | Usage |
|------|-----------|-------|
| `fullstack` | 8800-8849 | Full-stack development agents |
| `qa` | 8850-8899 | QA/testing agents |
| `ui` | 8900-8949 | UI/design agents |

Each agent picks the first available port in its range.

### Base Image

**Image**: `claude-sandbox:latest` (built from `Dockerfile.base`)

**Includes**:
- Python 3.11 + pip + venv
- Node.js 20 + pnpm
- Git
- Utilities: curl, jq, wget, build-essential
- Port: 8765 (default, overridable)

**Working directory**: `/app` (binds to git worktree)

## Quick Start

### 1. Start a Sandbox

```bash
./sandbox/scripts/sandbox-up.sh <ROLE> <WORKTREE_PATH> <AGENT_ID>
```

**Example:**
```bash
./sandbox/scripts/sandbox-up.sh fullstack /home/ubuntu/Claude agent-001
```

**Output:**
```
Starting sandbox for agent: agent-001 (role: fullstack)
...
Sandbox Setup Complete
========================================
Agent ID: agent-001
Role: fullstack
Port: 8800
Access: http://127.0.0.1:8800
```

### 2. Execute Commands Inside Sandbox

```bash
# Shell access
docker exec -it claude-sandbox-agent-001 bash

# Run a command
docker exec claude-sandbox-agent-001 pnpm run build

# View logs
docker logs claude-sandbox-agent-001
docker logs -f claude-sandbox-agent-001  # Follow logs
```

### 3. Stop and Clean Up

```bash
./sandbox/scripts/sandbox-down.sh agent-001
```

## Runtime Artifacts: `tmp/` Directory

Sandbox runtime artifacts (docker-compose files) are stored in `<project-root>/tmp/`,
which is gitignored. Never use system `/tmp/` for sandbox instances.

**Path resolution:** Each script resolves `PROJECT_ROOT` as `$(dirname $SANDBOX_ROOT)`
(one level up from `sandbox/`) and writes compose files to `$PROJECT_ROOT/tmp/`.

## Cleanup Lifecycle

After tests pass and the PR is merged to `dev`, run `sandbox-cleanup.sh` to tear down:

```bash
sandbox-cleanup.sh <AGENT_ID> [PR_NUMBER]
```

- With `PR_NUMBER`: verifies the PR is merged to `dev` before cleaning up
- Without `PR_NUMBER`: cleans up immediately

See `specs/sandbox.md` for the full lifecycle specification.

## Usage Details

### sandbox-up.sh

**Parameters:**
- `ROLE` (required): `fullstack`, `qa`, or `ui`
- `WORKTREE_PATH` (required): Absolute path to git worktree
- `AGENT_ID` (required): Unique identifier (e.g., `agent-001`, `qa-test-suite`)

**Behavior:**
1. Builds `claude-sandbox:latest` image (if needed)
2. Allocates port from role range via `pick-port.sh`
3. Generates `.docker-compose.AGENT_ID.yml` with:
   - Port binding to localhost
   - Worktree bind-mount (read-write)
   - Named volumes for `.venv` and `node_modules`
4. Starts container with `docker-compose up -d`
5. Waits for container readiness
6. Runs `ci-checks.sh` inside container:
   - TypeScript compilation (`pnpm run build`)
   - Python syntax validation (`py_compile`)
7. Reports status and access URL
8. **Returns exit code 0 if checks pass, 1 if checks fail**

**On failure:**
- Automatically calls `sandbox-down.sh` to clean up
- Removes compose file
- Exits with code 1

### sandbox-down.sh

**Parameters:**
- `AGENT_ID` (required): Must match the AGENT_ID from `sandbox-up.sh`

**Behavior:**
1. Finds and stops container `claude-sandbox-AGENT_ID`
2. Removes container and named volumes (`.venv`, `node_modules`)
3. Removes generated compose file from `tmp/`
4. Gracefully handles SIGINT/SIGTERM
5. **Always exits with code 0** (cleanup should not fail the caller)

### pick-port.sh

**Parameters:**
- `ROLE` (required): `fullstack`, `qa`, or `ui`

**Behavior:**
1. Defines port range for role
2. Checks availability via `/proc/net/tcp` (Linux)
3. Returns first available port
4. **Fails if all ports in range are in use**

**Exit codes:**
- 0: Port found (stdout contains port number)
- 1: All ports in use or invalid role

### ci-checks.sh

**Runs inside container** (called by `sandbox-up.sh`)

**Checks:**
1. **TypeScript compilation**: `cd dashboard/frontend && pnpm run build`
2. **Python syntax validation**: `py_compile` on all `.py` files in `dashboard/`
3. **Requirements validation**: Parses `dashboard/requirements.txt`

**Exit codes:**
- 0: All checks passed
- 1: One or more checks failed

**Output**: Colored summary (green/red) with passed/failed counts

### entrypoint.sh

**Manual startup** (not called by default in Phase 1):
```bash
docker exec -it claude-sandbox-agent-001 bash /app/sandbox/scripts/entrypoint.sh
```

**Starts**:
```bash
uvicorn dashboard.main:app --host 0.0.0.0 --port $PORT --reload
```

## Volumes

### Bind Mounts
- **Source**: Git worktree on host
- **Target**: `/app` in container
- **Mode**: `rw` (read-write)
- **Purpose**: Live code editing; changes on host are visible in container

### Named Volumes

**`.venv` isolation**:
- **Name**: `venv-{AGENT_ID}`
- **Target**: `/app/.venv` in container
- **Purpose**: Isolated Python environment per agent; persists across runs

**`node_modules` isolation**:
- **Name**: `node-modules-{AGENT_ID}`
- **Target**: `/app/node_modules` in container
- **Purpose**: Isolated Node dependencies per agent; prevents conflicts

## Environment Variables

**Set automatically by `sandbox-up.sh`:**
- `PORT`: Port assigned to this agent
- `ROLE`: Agent role (fullstack, qa, ui)
- `AGENT_ID`: Agent identifier
- `ENVIRONMENT`: Always "sandbox"

**Override examples**:
```bash
# In docker-compose or docker run
-e PORT=8765
-e ROLE=fullstack
-e AGENT_ID=my-agent
```

## Mock Fixtures

Located in `sandbox/fixtures/`:

### credentials.dashboard.mock.json
Mock credentials for dashboard (never contains real secrets):
```json
{
  "claude_api_key": "MOCK_NOT_REAL_CLAUDE_KEY_PLACEHOLDER",
  "twitter_api_key": "MOCK_NOT_REAL_TWITTER_KEY_PLACEHOLDER",
  ...
}
```

### env.dashboard.mock
Mock environment variables for dashboard:
```
STORAGE_STATE_PATH=./storage_state.json
LOG_LEVEL=INFO
ENVIRONMENT=sandbox
```

**Usage in containers**: Copy into container at startup:
```bash
docker cp sandbox/fixtures/env.dashboard.mock claude-sandbox-agent-001:/app/.env
```

## Debugging

### View Container Logs
```bash
# Last 50 lines
docker logs claude-sandbox-agent-001

# Follow logs in real-time
docker logs -f claude-sandbox-agent-001

# Last 100 lines with timestamps
docker logs --timestamps --tail 100 claude-sandbox-agent-001
```

### Shell Access
```bash
docker exec -it claude-sandbox-agent-001 bash
```

### Inspect Container
```bash
# Show full details
docker inspect claude-sandbox-agent-001

# Show network config
docker network inspect sandbox-fullstack

# Show volumes
docker volume inspect venv-agent-001
```

### View Port Allocations
```bash
# Check which ports are in use
netstat -tlnp | grep 8[89][0-9][0-9]

# Or use /proc/net/tcp directly
cat /proc/net/tcp | awk '{print $2}' | cut -d: -f2 | sort -u
```

## Validation (Phase 3)

✅ **Phase 3 adds comprehensive end-to-end validation** with three validation scripts:

### Validation Scripts

1. **`sandbox-test.sh`** — Single agent validation
   ```bash
   ./sandbox/scripts/sandbox-test.sh <ROLE> <AGENT_ID>
   ```
   Tests: startup, CI checks, container health, volume isolation, cleanup

2. **`parallel-test.sh`** — Multi-agent parallel execution
   ```bash
   ./sandbox/scripts/parallel-test.sh
   ```
   Tests: 3 agents (fullstack, qa, ui) running simultaneously, port collisions, concurrent CI checks

3. **`sandbox-cleanup-all.sh`** — Global cleanup
   ```bash
   ./sandbox/scripts/sandbox-cleanup-all.sh
   ```
   Tests: cleanup of all containers, orphaned volumes, and compose files

### Validation Coverage

- ✅ Single agent startup + CI checks
- ✅ Parallel multi-agent execution (3 roles, no conflicts)
- ✅ Port allocation (no collisions, role-based ranges)
- ✅ Graceful shutdown + cleanup
- ✅ Volume isolation (.venv, node_modules separate per agent)
- ✅ Worktree bind-mount (live editing)
- ✅ Global cleanup (sandbox-cleanup-all.sh)

See [`VALIDATION.md`](VALIDATION.md) for complete test documentation, commands, and troubleshooting.

## Limitations (Phase 1-3)

⚠️ **Known limitations**:

1. **No real credentials**: Mock fixtures only — sandbox cannot access real Claude API, Twitter API, or Obsidian vault
2. **HTTP only**: No HTTPS certificates (sandbox is isolated network)
3. **Static snapshot data**: No live data from external services

## File Structure Reference

```
claude-sandbox-agent-001/         # Container name (dynamic)
├── /app/                         # Bind mount (git worktree)
│   ├── dashboard/
│   │   ├── main.py
│   │   ├── runner.py
│   │   ├── requirements.txt
│   │   ├── frontend/
│   │   │   ├── package.json
│   │   │   ├── src/
│   │   │   └── dist/             # Build output
│   │   └── .venv/                # Named volume: venv-agent-001
│   ├── ~~agentic-twitter-claude/~~ (removed)
│   ├── ~~twitter-exporters/~~ (removed)
│   ├── sandbox/
│   │   ├── Dockerfile.base
│   │   ├── docker-compose.sandbox.yml
│   │   ├── scripts/
│   │   └── fixtures/
│   └── .git/
├── /app/node_modules/            # Named volume: node-modules-agent-001
├── /etc/                          # System config
└── /tmp/                          # Temp files
```

## Example Workflows

### Fullstack Agent: Frontend Build Test
```bash
# Start sandbox
./sandbox/scripts/sandbox-up.sh fullstack /home/ubuntu/Claude agent-fe-001

# Inside container, test build
docker exec claude-sandbox-agent-fe-001 bash -c "
  cd /app/dashboard/frontend
  pnpm run build
"

# Check build output
docker exec claude-sandbox-agent-fe-001 ls -la /app/dashboard/frontend/dist/

# Cleanup
./sandbox/scripts/sandbox-down.sh agent-fe-001
```

### QA Agent: Test Suite Execution
```bash
# Start QA sandbox
./sandbox/scripts/sandbox-up.sh qa /home/ubuntu/Claude agent-qa-001

# Run tests
docker exec claude-sandbox-agent-qa-001 bash -c "
  cd /app/dashboard
  python3 -m pytest tests/ -v
"

# Cleanup
./sandbox/scripts/sandbox-down.sh agent-qa-001
```

### Parallel Execution
```bash
# Start multiple agents in parallel
./sandbox/scripts/sandbox-up.sh fullstack /home/ubuntu/Claude agent-001 &
./sandbox/scripts/sandbox-up.sh qa /home/ubuntu/Claude agent-002 &
./sandbox/scripts/sandbox-up.sh ui /home/ubuntu/Claude agent-003 &

# Wait for all to complete
wait

# Cleanup all
for id in agent-001 agent-002 agent-003; do
  ./sandbox/scripts/sandbox-down.sh "$id"
done
```

## What's Next (Phase 4+)

- [ ] Integration with GitHub Actions workflow
- [ ] Agent orchestration (job runner)
- [ ] Real credentials support (sealed secrets)
- [ ] Health check endpoints
- [ ] Metrics collection (CPU, memory, duration)
- [ ] HTTPS support
- [ ] Multi-region deployment (if needed)

## Support & Troubleshooting

### Port Already in Use
```bash
# See which process is using a port
lsof -i :8800

# Check all sandbox ports
netstat -tlnp | grep 8[89][0-9][0-9]
```

### Container Won't Start
```bash
# Check if image exists
docker images | grep claude-sandbox

# Rebuild image if missing
docker build -f sandbox/Dockerfile.base -t claude-sandbox:latest sandbox/

# Check compose file (in tmp/)
cat tmp/.docker-compose.agent-001.yml
```

### CI Checks Failing
```bash
# Run checks manually inside container
docker exec -it claude-sandbox-agent-001 bash /app/sandbox/scripts/ci-checks.sh

# Check container logs
docker logs claude-sandbox-agent-001
```

### Volume Issues
```bash
# List all volumes
docker volume ls

# Inspect a volume
docker volume inspect venv-agent-001

# Remove orphaned volumes
docker volume prune
```

## References

- Docker: https://docs.docker.com/
- Docker Compose: https://docs.docker.com/compose/
- Python: https://www.python.org/
- Node.js: https://nodejs.org/

---

**Last updated**: Phase 1 implementation
**Status**: ✅ Foundational setup complete, Phase 2 in planning
