# Development Workflow

The sole development pipeline for **Agentic Software Boutique**.

## Pipeline stages

```
Issue → Plan → Dev (branch + PR) → CTO review → Human Owner Approval → CTO merge → QA → Close
```

### 1. Issue

- Every issue gets exactly one label: `bug`, `feature`, `security`, or `documentation`.
- The title should be descriptive (not "fix bug" but "Fix file upload payload size validation").

### 2. Plan

- CTO produces a brief plan in the issue: affected files, approach, risks.
- For features: include wireframe references or user-facing change description.

### 3. Dev

- Branch naming: `fix/<short-name>` or `feature/<short-name>`.
- One issue, one branch, one agent session at a time.
- Full Stack Developer implements following the plan.
- Validate before push:
  - `pnpm run build` (frontend compiles)
  - `pip install ruff && ruff check dashboard/` (backend lint)
  - `python3 -m py_compile dashboard/main.py` (backend syntax)
  - `pnpm run test` (frontend tests pass)
- Open PR against `main`.
- PR description references the issue: `Related to #N` (not `Closes #N`).

### 4. CTO Review

- CTO reviews every PR: architecture, standards, edge cases, security.
- If changes requested → Full Stack Developer amends on same branch.
- CTO marks "Approved" when ready.

### 5. Human Owner Approval

- Human must explicitly approve every merge to `main`. This gate is never skipped.
- The CTO presents a summary: what changed, what was tested, any risks.

### 6. CTO Merge

- After human approval, CTO merges the PR.
- Delete the branch after merge.

### 7. QA

- QA validates the merged code against the test plan from the issue.
- **Pass**: comment with verification detail, close the issue.
- **Fail**: reopen with exact failure detail and reproduction steps.

### 8. Close

- QA closes the issue after successful validation.

## Language rule

All text in this repository must be written in English. Exceptions:
- User-facing strings in the dashboard UI (which are in Spanish for the target audience)
- Documentation files explicitly marked as Spanish (`docs/README.md`)

## Deployment

After QA closes the issue, changes can be deployed to production:

```bash
# On the production VM
cd /path/to/deployment
git pull --ff-only
bash dashboard/start.sh   # idempotent — builds frontend, updates venv, reloads nginx+systemd
```

See `DEPLOYMENT.md` for detailed deployment guide, firewall rules, and monitoring.

## Pipeline exceptions

The full pipeline always applies unless the human owner explicitly instructs otherwise in writing (issue comment or direct message).
