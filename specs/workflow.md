# Development Workflow

The sole development pipeline for **Agentic Software Boutique**.

The authoritative source of truth is `specs/workflow.yaml`. This document describes the pipeline in prose.

## Agent Hierarchy

```
CTO ── launches agents, verifies workflows, approves PRs (post Tech Lead review),
│       sole authority for PRs to main
├── Tech Lead ── requests review loop, automated Code Review, reviews Security/UI-UX
│                findings, adds technical context, delegates to Dev (mandatory gate)
├── Full Stack Developer ── implements features/bugfixes
├── QA/Tester ── validates merged PRs against test plan, reopens on failure
├── Security Specialist ── pentesting, black box, SAST/DAST → creates Issue with findings
└── UI/UX Specialist ── design/UX review, accessibility audit → creates Issue with findings
     ↑
Advisory ── deep architecture review, only on CTO request (loop exhaustion, complex design)
```

## Pipeline stages

```
Issue → Plan (CTO) → Dev (branch + PR)
→ Tech Lead Code Review (automated, mandatory)
→ CTO approves → CTO merges to dev
→ QA → [Pass → CTO PR to main | Fail → loop]
→ Close
```

### 1. Issue

- Every issue gets exactly one label: `bug`, `feature`, `security`, or `documentation`.
- The title should be descriptive (not "fix bug" but "Fix file upload payload size validation").
- Security and UI/UX specialists create issues from their findings.

### 2. Plan

- CTO produces a brief plan in the issue: affected files, approach, risks.
- For features: include wireframe references or user-facing change description.

### 3. Dev

- Branch naming: `fix/<short-name>` or `feature/<short-name>`.
- One issue, one branch, one agent session at a time.
- Full Stack Developer implements following the plan.
- Validate before push:
  ```bash
  bash scripts/validate-workflow.sh
  ```
- Open PR against `dev`.
- PR description references the issue: `Related to #N` (not `Closes #N`).

### 4. Tech Lead Code Review

- Tech Lead reviews every PR automatically: architecture, standards, edge cases, security.
- References `specs/roles/tech-lead.md` for detailed review criteria.
- If changes requested → Full Stack Developer amends on same branch → re-review.
- When approved → marks "Tech Lead Approved".

### 5. CTO Review & Approval

- CTO reviews after Tech Lead approval.
- Verifies: Tech Lead approved, validate script passed, PR references issue, branch naming correct.
- Presents summary to human for approval when required.

### 6. CTO Merge

- After human approval (when required), CTO merges the PR to `dev`.
- Delete the branch after merge.
- Only CTO may create PRs from `dev` to `main`.

### 7. QA

- QA validates the merged code against the test plan from the issue.
- **Pass**: comment with verification detail, close the issue.
- **Fail**: reopen with exact failure detail and reproduction steps → triggers QA loop.

### 8. Close

- QA closes the issue after successful validation.

## Orchestration Loops

### QA Loop

```
QA fails → reopens issue → Tech Lead reviews → delegates to Dev
→ Dev fixes → re-QA
→ [Pass → close | Fail → counter++ → if counter >= max_retries → escalate]
```

- `max_retries` default: 3 (configurable in `specs/workflow.yaml`)
- On exhaustion: QA escalates to Tech Lead → Tech Lead relays to CTO + Advisory
- CTO + Advisory produce joint remediation plan → Tech Lead adds technical context → Dev implements → re-QA

### Security Loop

```
Security Specialist finds vuln → creates Issue
→ Tech Lead reviews, adds technical context, delegates to Dev
→ Dev fixes → Tech Lead Code Review → CTO approves → CTO merges → Security verifies → close
```

### UI/UX Loop

```
UI/UX Specialist finds issue → creates Issue
→ Tech Lead reviews, adds technical context, delegates to Dev
→ Dev fixes → Tech Lead Code Review → CTO approves → CTO merges → UI/UX verifies → close
```

## Language rule

All project artifacts MUST be written in English. This includes, without exception:
- Issue titles, descriptions, and comments
- PR titles, descriptions, comments, and reviews
- Commit messages
- Documentation (code comments, ADRs, guides, specs)
- Labels, milestones, and project board items

The only exception is user-facing strings in the dashboard UI, which may be translated for the target audience.

Internal communication between team members (this chat, voice calls) may use any language.

## Deployment

After QA closes the issue, changes from `dev` can be merged to `main` and deployed to production:

```bash
# On the production VM
cd /path/to/deployment
git checkout main && git pull --ff-only
bash dashboard/start.sh   # idempotent — builds frontend, updates venv, reloads nginx+systemd
```

See `DEPLOYMENT.md` for detailed deployment guide, firewall rules, and monitoring.

## Pipeline exceptions

The full pipeline always applies unless the human owner explicitly instructs otherwise in writing (issue comment or direct message).

See `specs/workflow.yaml` for the machine-readable definition.
See `specs/protocol.md` for agent-to-agent handoff and escalation protocol.
