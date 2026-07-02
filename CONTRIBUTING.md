# Contributing

## Development Workflow

```
Issue → Plan → Dev → CTO Review → Human Approval → CTO Merge → QA → Close
```

See [specs/workflow.md](specs/workflow.md) for complete details.

## Branching Strategy

- `main` — production-ready code
- `dev` — integration branch for feature work
- `feature/<name>` — feature branches, merged to `dev` via PR
- Direct commits to `main` or `dev` are not allowed

## Pull Request Process

1. Create a feature branch from `dev`
2. Implement your changes
3. Run lint and typecheck:
   ```bash
   ruff check dashboard/
   python3 -m py_compile dashboard/main.py
   cd dashboard/frontend && pnpm run build
   ```
4. Create a PR to `dev`
5. CTO reviews and approves
6. Human approves (when required)
7. CTO merges
8. QA validates
9. Issue is closed

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

## Temporary Files

Always use `tmp/` (project root) for temporary files — never `/tmp/`, `/dev/shm/`, or system temp directories. The `tmp/` directory is gitignored, project-scoped, and cleaned by `git clean`.

## License

By contributing, you agree that your contributions will be licensed under the project's license.
