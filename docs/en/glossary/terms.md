# Glossary

| Term | Definition |
|------|------------|
| **ADP** | Architecture Decision Record — a document capturing an architectural decision and its rationale |
| **Agent** | An AI-powered entity that can perform software development tasks (e.g., fix bugs, implement features) |
| **Agent Pool** | Registry of available agents with health monitoring |
| **Backend** | A `ChatBackend` implementation that wraps an AI CLI (Claude, OpenCode, etc.) for chat interaction |
| **Capability** | An interface defining what an agent can do (develop, review, QA, orchestrate) |
| **ChatBackend** | Abstract base class for pluggable AI conversation backends |
| **DAG** | Directed Acyclic Graph — used to model task dependencies in orchestration |
| **DOMPurify** | XSS sanitization library used on the frontend |
| **FastAPI** | Python web framework used for the backend API |
| **Headroom** | AI context compression and token optimization proxy |
| **Hermes** | Agent platform CLI for kanban, cron, curator, and skill management |
| **HSTS** | HTTP Strict-Transport-Security — forces HTTPS connections |
| **Kanban** | A task tracking system used for workflow management |
| **MCP** | Model Context Protocol — standard interface for exposing tools and resources to AI agents |
| **MCPServer** | Abstract base class for in-process MCP tool/resource servers |
| **Middleware** | ASGI middleware components for auth, HSTS, tracing, and rate limiting |
| **Obsidian** | Markdown note-taking application; the platform can browse Obsidian vaults |
| **OpenCode** | A coding agent CLI; one of the supported chat backends |
| **Orchestrator** | System that decomposes goals into task graphs and delegates to agents |
| **Ponytail** | A lazy-development philosophy prioritizing minimal working solutions |
| **Rate Limiting** | Per-endpoint request throttling via slowapi |
| **Sandbox** | Docker-based isolated environment for running agents |
| **SPA** | Single Page Application — the React frontend |
| **SQLite** | Embedded database engine used for persistence |
| **SSE** | Server-Sent Events — used for streaming job logs and task events |
| **SubTask** | A single unit of work within a task graph |
| **systemd** | Linux init system used to manage the uvicorn process |
| **Tailwind v4** | CSS framework used for frontend styling |
| **Task Graph** | A DAG of subtasks with dependencies for multi-agent execution |
| **Token Accounting** | Tracking of LLM token usage across the platform |
| **uvicorn** | ASGI server used to run the FastAPI application |
| **Vault** | An Obsidian vault directory containing Markdown notes |
| **Vitest** | Unit test framework for the frontend |
| **WAL mode** | Write-Ahead Logging — SQLite mode for better concurrent access |
| **Workflow** | A multi-step process definition that can be loaded and executed |
