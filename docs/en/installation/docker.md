# Docker Installation

> Docker support is limited to the sandbox environment for agent isolation. The main application is not containerized — running it with `uvicorn` directly is the standard approach.

## Sandbox Containers

The `sandbox/` directory provides Docker-based isolation for running agents in parallel. See `sandbox/README.md` for details.

### Prerequisites

```bash
sudo apt install docker.io
sudo usermod -aG docker $USER
# Log out and back in
```

### Usage

```bash
# Start a sandbox container
bash sandbox/sandbox-up.sh <role>

# Stop a sandbox
bash sandbox/sandbox-down.sh <role>

# Check status
bash scripts/check-sandboxes.sh
```

## Production Deployment

For production, see the [Deployment Guide](../deployment/production.md) — it uses systemd + nginx, not Docker.
