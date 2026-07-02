# Contributing

## Development Workflow

```
Issue → Plan (CTO) → Dev (branch + PR)
→ Tech Lead Code Review (mandatory gate)
→ CTO approves → CTO merges to dev
→ QA → [Pass → CTO PR to main | Fail → loop]
→ Close
```

See [specs/workflow.md](specs/workflow.md) and [specs/workflow.yaml](specs/workflow.yaml) for complete details.

## Workflow Protocol (Non-negotiable)

The development pipeline is a **machine-enforced protocol** defined in `specs/workflow.yaml`. Every agent must follow the defined stages in order, verify pre/postconditions at each stage, and use the handoff protocol from `specs/protocol.md` for agent-to-agent communication.

## Branching Strategy

- `main` — production-ready code
- `dev` — integration branch for feature work
- `feature/<name>` — feature branches, merged to `dev` via PR
- Direct commits to `main` or `dev` are not allowed

## Pull Request Process

1. Create a feature branch from `dev`
2. Implement your changes
3. **Run validation**:
   ```bash
   bash scripts/validate-workflow.sh
   ```
4. Create a PR to `dev` using the PR template (`.github/PULL_REQUEST_TEMPLATE.md`)
5. Tech Lead Code Review (mandatory gate)
6. CTO reviews and approves (after Tech Lead approval)
7. Human approves (when required)
8. CTO merges to `dev`
9. QA validates against test plan
10. QA passes → CTO creates PR from `dev` to `main`
11. Issue is closed

## Commit Conventions

Use clear, descriptive commit messages:

```
<area> — <brief description>
```

Examples:
- `agents — add codex backend stub`
- `docs — translate architecture page to Spanish`
- `fix — resolve path traversal in notes endpoint`

## Coding Standards

### Python
- Type hints required for all function signatures
- Follow ruff linting rules (configured in `pyproject.toml`)
- One class per file for significant types
- Use ABCs for interfaces

### TypeScript / React
- Strict TypeScript mode
- Functional components with hooks (no class components)
- Tailwind v4 for styling (CSS-first, no `tailwind.config.ts`)
- Descriptive component names

## Documentation Requirements

**Every new feature must include documentation in both English and Spanish.**

The documentation structure mirrors across languages:
- `docs/en/` — English documentation
- `docs/es/` — Spanish documentation

All documentation files must maintain identical:
- Directory structure
- Filenames
- Headings and sections
- Diagrams and tables
- Internal links

Use only Markdown — no HTML, no GitHub Wiki.

## Issue Reporting

- Use GitHub issues for bug reports, feature requests, and tasks
- Every issue gets exactly one label: `bug`, `feature`, `security`, or `documentation`
- Include steps to reproduce for bugs
- Include acceptance criteria for features

## Git Hooks (Mandatory Setup)

After cloning, install the pre-push hook:

```bash
git config core.hooksPath .githooks
```

This runs `scripts/validate-workflow.sh` (ruff + py_compile + pnpm build + pnpm test + branch naming) on every push to feature/fix branches. To skip: `git push --no-verify`.

## Temporary Files

Always use `tmp/` (project root) for temporary files — never `/tmp/`, `/dev/shm/`, or system temp directories. The `tmp/` directory is gitignored, project-scoped, and cleaned by `git clean`.

## License

By contributing, you agree that your contributions will be licensed under the project's license.
