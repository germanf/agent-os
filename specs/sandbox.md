# Sandbox Convention: Isolated Environments per Agent

When multiple implementation agents run in parallel on the same repo, they need isolation to avoid stomping on each other's files, ports, and state. Two complementary mechanisms, not mutually exclusive:

## 1. Git Worktree per Agent

Each agent works in its own `git worktree` (its own branch, its own directory), not in the main checkout. This prevents two concurrent agents from interfering with each other's `git checkout` or commits.

**Known risk — verify, do not assume:** some "worktree isolation" mechanisms do not reliably guarantee that the agent never ends up operating on the shared main directory. After an agent with isolation finishes, confirm with `git worktree list` and `git status` in the main directory that it is actually intact — do not assume it just because isolation was requested.

**Cleanup order matters:** if there is also a container (see section 2) with a bind-mount to the worktree, stop the container *before* removing the worktree. If the worktree disappears first, the container can be left with hanging processes pointing to a directory that no longer exists.

## 2. Docker Containers per Role, with Fixed Port Ranges

If the project supports it, each role runs in its own container with its own port range — prevents collisions when multiple agents are active simultaneously. Example convention (numbers are illustrative — choose what makes sense for your setup):

| Role | Port Range (example) | Data Access |
|---|---|---|
| Full Stack Developer | 8800–8849 | Read-write code, mocked credentials |
| QA/Tester | 8850–8899 | Read-only, data snapshot (not real production) |
| UX/UI Designer | 8900–8949 | Read-write frontend, read-only backend |

**Credentials:** always mocked inside the sandbox — never real credentials or production data, not even read-only. Network/port isolation does not substitute for data isolation.

## When This Is Not Needed

If you work with a single agent at a time (no real parallelism), a worktree alone is enough to keep git history clean. Docker containers are for when there is real port/process collision from running multiple things simultaneously — not a universal requirement.

Related roles: [Full Stack Developer](roles/fullstack-developer.md) · [QA/Tester](roles/qa-tester.md)
