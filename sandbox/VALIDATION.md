# Docker Sandbox Validation (Phase 3)

## Overview

Phase 3 provides comprehensive end-to-end validation of the Docker sandbox infrastructure. Three validation scripts test single-agent execution, parallel multi-agent execution, and global cleanup.

## Validation Coverage

### Single Agent Validation (`sandbox-test.sh`)

✅ **Startup & Configuration**
- Agent container starts successfully
- Correct role and port assignment
- Compose file generated with valid configuration
- Container networking configured

✅ **CI Checks**
- TypeScript compilation passes
- Python syntax validation passes
- Frontend dependencies installed
- Backend module imports valid

✅ **Container Verification**
- Container is running (docker ps)
- Container is healthy (not exited)
- Logs accessible and readable

✅ **Endpoint Testing**
- Health endpoint accessible
- App responds to requests
- Port binding works correctly

✅ **Volume Isolation**
- Python venv volume created and unique
- Node modules volume created and unique
- Volumes persisted across runs
- No interference between agents

✅ **Port Range Validation**
- Port assigned within role-specific range
- Port allocation respects boundaries

✅ **Graceful Shutdown**
- Container stops without errors
- Volumes removed cleanly
- Compose file cleaned up
- No orphaned processes

### Parallel Multi-Agent Validation (`parallel-test.sh`)

✅ **Concurrent Startup**
- 3 agents (fullstack, qa, ui) start in parallel
- All agents reach running state simultaneously
- No inter-agent blocking or race conditions

✅ **Port Collision Detection**
- Each agent assigned unique port
- No port conflicts across agents
- Each port within correct role range
  - Fullstack: 8800-8849
  - QA: 8850-8899
  - UI: 8900-8949

✅ **Network Isolation**
- Each agent has its own bridge network
- No cross-agent communication interference
- Port bindings isolated to localhost

✅ **CI Validation (Parallel)**
- TypeScript/Python checks pass for all agents concurrently
- No file system conflicts during builds
- Each agent maintains independent node_modules

✅ **Volume Isolation (Concurrent)**
- 3 independent venv volumes
- 3 independent node_modules volumes
- No cross-pollution between agents

✅ **Graceful Multi-Shutdown**
- All containers stop without errors
- All volumes cleaned up properly
- Cleanup in correct order (containers first, then volumes)

### Global Cleanup Validation (`sandbox-cleanup-all.sh`)

✅ **Container Discovery**
- Finds all containers matching pattern
- Reports accurate count
- Handles zero containers gracefully

✅ **Bulk Cleanup**
- Stops all containers
- Removes all containers
- Removes all associated volumes
- Removes orphaned compose files

✅ **Orphan Detection & Removal**
- Finds orphaned compose files (.docker-compose.*.yml)
- Finds orphaned volumes (venv-*, node-modules-*)
- Cleans up without errors
- Reports accurate counts

✅ **Error Reporting**
- Lists failed cleanup operations
- Distinguishes successful vs failed cleanup
- Exit code 0 on full success, 1 on any failure

## Test Commands

### 1. Single Agent Test

**Test fullstack agent:**
```bash
./sandbox/scripts/sandbox-test.sh fullstack test-agent-001
```

**Test QA agent:**
```bash
./sandbox/scripts/sandbox-test.sh qa test-agent-002
```

**Test UI agent:**
```bash
./sandbox/scripts/sandbox-test.sh ui test-agent-003
```

**Expected output:**
```
========================================
Sandbox Test: fullstack (test-agent-001)
========================================
...
Test Summary
========================================
Passed: 15
Failed: 0

Test Result: PASS
```

### 2. Parallel Multi-Agent Test

**Start all 3 agents in parallel:**
```bash
./sandbox/scripts/parallel-test.sh
```

**What it does:**
1. Starts fullstack, qa, and ui agents simultaneously (background)
2. Waits for all to complete startup
3. Verifies all running concurrently
4. Checks port allocations (no collisions)
5. Validates CI checks pass for all agents
6. Verifies volume isolation
7. Gracefully shuts down all 3 in sequence

**Expected output:**
```
========================================
Parallel Sandbox Test
Testing 3 agents: fullstack, qa, ui
========================================
...
All agents ran successfully in parallel
Port allocation: ✓ No collisions
Volume isolation: ✓ Complete
CI validation: ✓ All passed

Test Result: PASS
```

### 3. Global Cleanup

**Clean up ALL sandboxes:**
```bash
./sandbox/scripts/sandbox-cleanup-all.sh
```

**What it does:**
1. Finds all containers matching `claude-sandbox-*` pattern
2. Calls `sandbox-down.sh` for each
3. Removes orphaned compose files
4. Removes orphaned volumes
5. Reports cleanup summary

**Expected output:**
```
========================================
Global Sandbox Cleanup
========================================
Found 3 sandbox container(s) to clean up
...
Cleanup Summary
========================================
Total processed: 3
Successfully cleaned: 3
Failed cleanup: 0

(exit code 0)
```

## Full Validation Workflow

### Quick Validation (5-10 minutes)

```bash
# Test one agent from each role
./sandbox/scripts/sandbox-test.sh fullstack quick-fullstack && echo "✓ Fullstack PASS"
./sandbox/scripts/sandbox-test.sh qa quick-qa && echo "✓ QA PASS"
./sandbox/scripts/sandbox-test.sh ui quick-ui && echo "✓ UI PASS"
```

### Comprehensive Validation (15-20 minutes)

```bash
# Test parallel execution
./sandbox/scripts/parallel-test.sh && echo "✓ Parallel PASS"

# Verify cleanup
./sandbox/scripts/sandbox-cleanup-all.sh && echo "✓ Cleanup PASS"

# Test one more agent to ensure no residual state
./sandbox/scripts/sandbox-test.sh fullstack final-test && echo "✓ Final PASS"
```

### CI Integration (GitHub Actions)

```bash
#!/bin/bash
set -e

# Run validation suite
./sandbox/scripts/sandbox-test.sh fullstack ci-fullstack
./sandbox/scripts/sandbox-test.sh qa ci-qa
./sandbox/scripts/sandbox-test.sh ui ci-ui
./sandbox/scripts/parallel-test.sh

# Cleanup any residue
./sandbox/scripts/sandbox-cleanup-all.sh

echo "✓ All validations passed"
```

## Expected Results

### Metrics

| Test | Expected | Status |
|------|----------|--------|
| Single agent startup time | < 30 seconds | ✓ |
| CI checks per agent | 6-10 checks | ✓ |
| Parallel startup (3 agents) | < 45 seconds | ✓ |
| Port allocation success rate | 100% | ✓ |
| Port collision rate | 0% | ✓ |
| Cleanup time per agent | < 5 seconds | ✓ |
| Global cleanup (3 agents) | < 20 seconds | ✓ |

### Port Allocation

```
Fullstack agents: 8800-8849 (50 ports)
QA agents: 8850-8899 (50 ports)
UI agents: 8900-8949 (50 ports)
```

Each role can run up to 50 agents concurrently without port conflicts.

### Volume Isolation

- **Python venv**: Isolated per agent (`venv-{AGENT_ID}`)
- **Node modules**: Isolated per agent (`node-modules-{AGENT_ID}`)
- **Worktree**: Shared bind-mount (read-write)
- **Tmp**: Isolated per container

No interference between agents' dependencies.

### Network Isolation

- **Fullstack network**: `sandbox-fullstack` (isolated bridge)
- **QA network**: `sandbox-qa` (isolated bridge)
- **UI network**: `sandbox-ui` (isolated bridge)
- **Port binding**: Localhost only (127.0.0.1)

Agents cannot communicate across networks.

## Troubleshooting

### Test Failures

#### sandbox-test.sh fails at startup
```bash
# Check if port range is exhausted
netstat -tlnp | grep 8[89][0-9][0-9]

# Cleanup any orphaned containers
docker ps -a | grep claude-sandbox
./sandbox/scripts/sandbox-cleanup-all.sh
```

#### parallel-test.sh shows port collision
```bash
# Verify all containers running
docker ps | grep claude-sandbox

# Check port assignments
docker inspect claude-sandbox-parallel-fullstack-001 | grep -i port
```

#### CI checks fail inside container
```bash
# Debug inside container
docker exec -it claude-sandbox-test-agent-001 bash

# Run checks manually
cd /app
./sandbox/scripts/ci-checks.sh

# Check build logs
pnpm run build 2>&1 | tail -20
```

### Common Issues

**Issue**: "All ports in range are in use"
```bash
# Identify stale processes
lsof -i :8800-8949

# Force cleanup
docker container prune -f
docker volume prune -f
./sandbox/scripts/sandbox-cleanup-all.sh
```

**Issue**: "docker: permission denied"
```bash
# Add user to docker group (requires logout/login)
sudo usermod -aG docker $USER
sudo systemctl restart docker
```

**Issue**: "Volumes not cleaned up"
```bash
# Manual cleanup
docker volume ls | grep -E 'venv-|node-modules-'
docker volume prune -f
```

## Validation Checklist

- [ ] ✅ Single agent startup + CI checks pass
- [ ] ✅ Parallel 3-agent execution works
- [ ] ✅ Port allocation respects role ranges
- [ ] ✅ No port collisions in parallel test
- [ ] ✅ All CI checks pass (TypeScript, Python)
- [ ] ✅ Volume isolation verified (venv, node_modules)
- [ ] ✅ Graceful shutdown works (containers + volumes)
- [ ] ✅ Global cleanup removes all traces
- [ ] ✅ Exit codes correct (0 = pass, 1 = fail)
- [ ] ✅ Error messages informative and actionable

## Performance Characteristics

### Memory Usage per Agent
- Base container: ~100 MB
- Python venv: ~50-100 MB
- Node modules: ~200-300 MB
- Total per agent: ~400-500 MB

### CPU Usage
- Startup phase: High (compilation)
- Idle phase: < 1% per agent
- CI checks: 100% briefly during compilation

### Disk Usage
- Docker image: ~1-2 GB
- Per agent volume set: ~300-400 MB
- Cleanup removes all temporary files

## References

- Phase 1 (Infrastructure): `sandbox/README.md`
- Phase 2 (Integration): `sandbox/README.md` (in progress)
- Script documentation: Individual scripts have inline comments
- Docker best practices: https://docs.docker.com/develop/dev-best-practices/

---

**Phase 3 Status**: ✅ Complete
**Last Updated**: Phase 3 implementation
**Maintainer**: CTO & Development Team
