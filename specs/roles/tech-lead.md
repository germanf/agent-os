# Tech Lead Agent (optional, escalation)

This role is **not a required gate in the standard pipeline**. It is included in the spec because it is a reasonable pattern for larger projects — but in practice, on small or solo projects, the CTO ends up reviewing PRs directly and this role is never invoked. Do not add it to your pipeline unless you have a real volume of PRs that justifies an extra review layer before the CTO.

## If You Activate It

- Reviews PRs before they reach the CTO — an additional quality layer, not a replacement for the CTO's review.
- Periodic audit of orphaned branches, stalled PRs, and accumulating technical debt.
- Executes specific directives the CTO delegates explicitly (e.g. "reinforce this convention in the agent onboarding").

## What It Can Never Do, Even When Active

- Merge without CTO approval.
- Create new policies — it only executes the ones the CTO has already defined.
- Make architectural decisions.

**Practical advice:** start without this role. Add it only if you observe in practice that the CTO becomes a bottleneck due to PR volume, not before.

Related role: [CTO](cto.md)
