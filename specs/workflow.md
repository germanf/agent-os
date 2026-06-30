# Development Workflow

Issue → Plan → Dev (branch + PR) → CTO review → **human owner approval** → CTO merge → QA → close.

This is the only pipeline. If you modify it, update this file in the same change — a "real" pipeline that lives only in agents' memory and not in a versioned doc will diverge from what is actually done.

## Step 0 — Issue + Plan (before writing any code)

- Every bug or feature has an issue. Required category labels (permanent — never removed): `bug`, `feature`, `security`, `documentation`. You can add more, but these four should always be present.
- The CTO comments a brief plan on the issue before delegating: root cause (for bugs), files to touch, technical constraints. This is not bureaucracy — it is what prevents the implementer from redesigning on the fly and drifting from scope.
- Branch naming convention: `fix/<short-name>` for bugs, `feature/<short-name>` for features.

## Step 1 — Dev (Full Stack Developer Agent)

- Branch from main, following the plan from step 0.
- Implement, validate locally (build/tests, or the sandbox environment if the project has one — see [sandbox.md](sandbox.md)).
- Push the branch and **open the PR** — the implementer writes the description because they have the full context of the diff. The PR references the issue but does not close it (`Related to #N`, not `Closes #N`) — the issue is closed by QA after validation, not by the merge.

## Step 2 — CTO (Code Review)

- Reviews correctness, security, and style.
- If there are comments, the Dev resolves them and the CTO reviews again — a PR with unresolved comments does not get merged, no exceptions of "merge now, fix later."
- If everything is OK, moves to step 2.5 — **the CTO does not merge yet**, even after technical approval.

## Step 2.5 — Human Owner Approval (the gate that is never skipped)

This is the highest-consequence step in the entire pipeline, and it is deliberately manual.

**Why it exists despite the CTO having full technical authority:** the CTO's authority covers technical decisions — architecture, how something is implemented. It does not replace the human owner as the gate for what reaches production. These are different axes: "is it well built?" vs. "do I want this to exist in the world, now, like this?" — and the second is a decision the owner has never delegated, not even when delegating everything technical.

The cost of asking for this approval is low (one message, one response). The cost of merging without it, if the owner did not want it, is not reversible in the same way — the code has already run, deployed, taken effect. That asymmetry is the fundamental reason for this gate, not bureaucracy for its own sake.

**How to skip it, if ever appropriate:** only with an explicit and specific instruction from the human owner — "merge this without asking me" in that specific moment, or a standing authorization like "merge whatever you approve, don't consult me each time" stated clearly. A vague general phrase ("handle everything," "you decide") does **not** count as that authorization — if there is real ambiguity about whether the owner meant this, ask; do not assume.

## Step 3 — CTO Merge

Once the human owner approves: the CTO merges, and if the project uses status labels, marks the issue as ready for QA (e.g. `ready-to-test`).

## Step 4 — QA/Tester

Executes the issue's test plan against the already-merged code, with real evidence (see [qa-tester.md](roles/qa-tester.md)). If it passes, closes the issue. If it fails, reopens it with the exact detail of the failure — the cycle returns to step 1. An issue is never closed without passing its own test plan.

## Exceptions

The full pipeline (including step 2.5) always applies, unless the human owner gives an explicit instruction to the contrary for that specific case ("push directly to main," "no PR," "skip the plan"). Without that instruction, the full flow is the rule, not the exception.

Roles involved: [CTO](roles/cto.md) · [Full Stack Developer](roles/fullstack-developer.md) · [QA/Tester](roles/qa-tester.md) · [UX/UI Designer](roles/ux-ui-designer.md) (advisory, non-blocking) · [Tech Lead](roles/tech-lead.md) (optional, not wired in by default)
