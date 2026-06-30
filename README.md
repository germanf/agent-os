# agent-os

A generic environment for AI-assisted software development with Claude Code — not tied to any specific domain or project.

## What it includes

- `specs/` — role definitions (CTO, Full Stack Developer, QA/Tester, UX/UI Designer), the development pipeline (issue → plan → PR → review → merge → QA), and sandbox isolation conventions.
- `sandbox/` — scripts to run agents in isolated Docker containers, with per-role port ranges and access permissions.
- Self-hosted runner pattern for automatic deployment (config/docs — you bring your own infrastructure; no real runner or VM is included).
- Interface features (planned): browser-based chat with Claude Code, and a Markdown note browser (Obsidian-compatible).

## What it does NOT include

Anything specific to any particular project: credentials, personal vaults, domain-specific logic, or real infrastructure. Fork this and wire up your own.

## Status

`specs/` — complete (Phase 1).  
`sandbox/` — complete.  
Interface features (`/chat`, `/notes`) — planned (Phase 2).  
Making the repo public — pending, separate decision.
