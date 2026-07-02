# Project Overview

## What is Agentic Software Boutique?

Agentic Software Boutique (agent-os) is a **generic, domain-agnostic platform for AI-assisted software development**. It provides a web dashboard, multi-agent orchestration, a Model Context Protocol (MCP) tool ecosystem, and a pluggable backend system for interacting with various AI coding agents.

The platform is designed to be wired to any project — you bring your own codebase, credentials, and infrastructure.

## Vision

Enable AI agents to collaborate on software development tasks with human oversight, using a lean, modular platform that stays out of the way. The best code is the code never written.

## Philosophy

- **Agent-agnostic**: works with Claude, Codex, Kimi, OpenCode — any backend implementing the `ChatBackend` protocol
- **Protocol-first**: MCP as standard tool exposure interface
- **Graceful degradation**: every feature works without MCP servers, multi-agent, or any optional component
- **Observability by default**: structured logs, metrics, health checks on all components
- **Incremental deployability**: every sub-phase deployable independently to production

## High-Level Concepts

| Concept | Description |
|---------|-------------|
| Dashboard | FastAPI + React SPA for monitoring and interaction |
| Chat Backend | Pluggable subprocess backend for AI conversation (Claude, Codex, etc.) |
| Agent Pool | Registry of available AI agents for task delegation |
| Task Graph | DAG-based multi-step task execution with dependencies |
| MCP Server | In-process tool/resource server for AI agent consumption |
| Kanban | Workflow tracking via Hermes kanban integration |
| Headroom | Context compression and token optimization proxy |
| Sandbox | Docker-based isolated agent execution environments |

## Design Principles

- No big-bang deployments — every change is independently deployable
- All external dependencies are optional — the system degrades gracefully
- Secrets never hardcoded, logged, or committed
- Lazy evaluation — ponytail mode prioritizes minimal working solutions
