# CLI Reference

## External CLIs

The platform interacts with several external CLIs. These are not bundled — they must be installed separately.

### Hermes

The Hermes agent platform CLI manages kanban boards, cron jobs, skills, and curator reviews.

```bash
# Kanban
hermes kanban list
hermes kanban create --queue "Phase 5" --title "Task"
hermes kanban complete <id>

# Cron
hermes cron list
hermes cron create --schedule "0 9 * * *" --command "..."

# Curator
hermes curator run

# Skills
hermes skills list
hermes skills install <path>
```

### Claude Code

```bash
claude -p "implement feature X"                      # One-shot
claude -p "continue" --resume <session>               # Resume conversation
claude -p "explain this code" --output-format stream-json  # For programmatic use
```

### Headroom

Context compression and token optimization proxy:

```bash
headroom                                       # Start proxy
headroom remember "important context"          # Store in memory
headroom recall                                # Retrieve context
headroom learn                                 # Learn from patterns
headroom status                                # Proxy status
```

### OpenCode

```bash
opencode serve --port 8899                     # Start server
opencode run "implement feature"               # One-shot task
```

## Internal Commands

### Backend

```bash
uvicorn dashboard.main:app --port 8765 --reload                    # Dev server
python3 -m py_compile dashboard/main.py                             # Syntax check
ruff check dashboard/                                                # Lint
```

### Frontend

```bash
pnpm run dev         # Dev server (port 5173, proxies to backend)
pnpm run build       # Production build
pnpm run test        # Run tests
pnpm run lint        # ESLint
```

### Deployment

```bash
bash dashboard/start.sh   # Full production deploy (idempotent)
bash dashboard/restore.sh # Restore DB from backup
bash dashboard/diagnose.sh # VM diagnostics (Spanish)
```
