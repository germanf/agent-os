# System Architecture

Agent hierarchy, orchestration flow, and handoff routes for **Agentic Software Boutique**.

## Agent Hierarchy

```
                        ┌───────────────────────┐
                        │      Human Owner       │
                        │  (roadmap, approval)   │
                        └───────────┬───────────┘
                                    │
                        ┌───────────▼───────────┐
                        │         CTO           │
                        │  launches agents      │
                        │  verifies workflows   │
                        │  approves PRs         │
                        │  sole PR-to-main      │
                        └───┬───────┬───────┬───┘
                            │       │       │
              ┌─────────────┘       │       └─────────────┐
              │                     │                     │
   ┌──────────▼──────────┐  ┌──────▼──────┐  ┌───────────▼───────────┐
   │     Tech Lead       │  │  Advisory   │  │   Full Stack Dev     │
   │  Code Review (gate) │  │ deep review │  │  implementation      │
   │  Security/UI-UX     │  │ loop exhaust│  │  feature/bugfix      │
   │  triage & delegate  │  │ arch review │  │                      │
   └─────────────────────┘  └─────────────┘  └───────────────────────┘
              │
     ┌────────┼────────┐
     │        │        │
┌────▼───┐ ┌──▼───┐ ┌──▼───────┐
│  QA/   │ │ Sec  │ │ UI/UX    │
│ Tester │ │ Spec │ │ Specialist│
│ valida-│ │ pent-│ │ design/  │
│ tion   │ │ est  │ │ access.  │
└────────┘ └──────┘ └──────────┘
```

## Orchestration Flow (Main Pipeline)

```
        ┌──────────┐
        │  Issue   │
        └────┬─────┘
             │
        ┌────▼─────┐
        │  Plan    │ ← CTO
        └────┬─────┘
             │
        ┌────▼─────┐
        │   Dev    │ ← Full Stack Developer (branch: feature/* or fix/*)
        └────┬─────┘
             │
        ┌────▼─────────┐
        │ Tech Lead    │ ← Automated Code Review
        │ Code Review  │
        └────┬─────────┘
             │
        ┌────▼─────────┐
        │ CTO Review & │ ← Verifies Tech Lead approved, validations pass
        │ Approval     │
        └────┬─────────┘
             │
        ┌────▼─────┐
        │ CTO Merge│ → to dev, delete branch
        └────┬─────┘
             │
        ┌────▼─────┐
        │    QA    │ ← Validate against test plan
        └────┬─────┘
             │
     ┌───────┴───────┐
     │               │
  [Pass]          [Fail] ──→ QA Loop (counter++)
     │               │
┌────▼─────┐   ┌─────┴──────┐
│ Close    │   │ Counter >= │
│          │   │ max_retries│
└────┬─────┘   │ (default 3)│
     │         └─────┬──────┘
┌────▼──────┐        │
│ CTO PR to │   ┌────▼──────────────┐
│ main      │   │ Escalate: QA → TL │
└───────────┘   │ → CTO + Advisory  │
                │ → Plan → TL adds  │
                │ context → Dev fix │
                │ → re-QA           │
                └───────────────────┘
```

## Handoff Routes

| From | To | Trigger |
|------|----|---------|
| Full Stack Developer | Tech Lead | Blocker, ambiguous spec |
| Tech Lead | Full Stack Developer | Issue triaged, ready for implementation |
| Tech Lead | CTO | Code Review complete (approved), escalation relay |
| QA/Tester | Tech Lead | QA loop exhausted (3 failures) |
| QA/Tester | Tech Lead | QA fail (loop iteration, < max_retries) |
| Security Specialist | Tech Lead | Creates Issue with findings |
| UI/UX Specialist | Tech Lead | Creates Issue with findings |
| CTO | Tech Lead | Plan ready (add technical context) |
| CTO + Advisory | Tech Lead | Remediation plan (post loop exhaustion) |
| CTO | Full Stack Developer | Direct delegation (only if Tech Lead unavailable) |

## State Machine

Each workflow stage has four states: `pending`, `running`, `completed`, `failed`.

Stage transitions:

```
pending → running (when preconditions met)
running → completed (when postconditions met)
running → failed (on error or precondition violation)
completed → running (loop iteration — QA fail reopens)
failed → pending (after remediation plan)
```

Loops maintain a counter. When `counter >= max_retries`, the stage transitions to `failed` and triggers escalation instead of another loop iteration.

See `specs/workflow.yaml` for machine-readable stage definitions.
See `specs/protocol.md` for handoff message formats.
