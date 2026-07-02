# Changelog

## Release Strategy

The project uses **linear versioning** based on development phases:

- **Phase 1**: Foundation (specs, sandbox)
- **Phase 2**: Chat + Notes interface
- **Phase 3**: Memory, skills, learning
- **Phase 4**: Full platform — memory, observability, self-improvement
- **Phase 5**: Production ready — multi-agent, MCP, hardening, frontend & UX

Each phase is delivered as a set of GitHub issues, each closed by a pull request to the `dev` branch. The `main` branch represents production-ready code.

## Phase 5 (Latest)

| Issue | Description | PR |
|-------|-------------|-----|
| #71 | Multi-Agent Orchestration — Task Graph, Agent Pool, Executor, SSE | #78 |
| #72 | MCP Ecosystem — 4 MCP servers, Registry, Admin UI | #79 |
| #73 | Production Hardening — Alerts, Backup, Rate Limits, Runbook | #77 |
| #74 | Frontend & UX — Landing, Dashboard, UI Components, Breadcrumbs | #80 |
| #68 | Self-Improving Platform Skills — 5 SKILL.md files, curator loop | #69 |

## Phase 4

| Issue | Description |
|-------|-------------|
| #27 | Memory system (project/org stores) |
| #28 | OpenTelemetry tracing |
| #29 | Token accounting |
| #30 | Headroom integration |
| #31 | Hermes kanban adapter |
| #32 | Approval workflows |
| #33 | Job checkpoints and resumption |
| #34 | Notifications and alerting |
| #35 | Cron job management |

## Phase 3

| Issue | Description |
|-------|-------------|
| — | Headroom context compression |
| — | Hermes curator review loop |
| — | Platform skill definitions |
| — | Ponytail plugin |

## Phase 2

| Issue | Description |
|-------|-------------|
| — | Chat interface with Claude |
| — | Obsidian vault browser |
| — | File upload for chat |
| — | Multi-backend support |

## Phase 1

| Issue | Description |
|-------|-------------|
| — | Project scaffolding |
| — | FastAPI backend |
| — | React frontend |
| — | Sandbox containers |
| — | Auth middleware |
| — | Rate limiting |
| — | Deployment scripts |
