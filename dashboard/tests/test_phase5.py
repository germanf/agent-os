#!/usr/bin/env python3
"""Smoke test: Phase-5 modules import without errors."""

def check(label: str) -> None:
    try:
        exec(f"from dashboard.{label} import *")
        print(f"  ✓ {label}")
    except Exception as e:
        print(f"  ✗ {label}: {e}")
        raise


def main():
    print("Phase-5 import smoke test")
    print()

    modules = [
        "mcp.client",
        "mcp.server",
        "mcp.servers.kanban",
        "mcp.servers.memory",
        "mcp.servers.notes",
        "mcp.servers.workflows",
        "agents.protocol",
        "agents.opencode_agent",
        "agents.hermes_agent",
        "agents.reviewer",
        "agents.security_agent",
        "agents.uiux_agent",
        "workflow",
        "orchestrator.agent_pool",
        "orchestrator.executor",
        "orchestrator.task_graph",
        "orchestrator.aggregator",
    ]

    for m in modules:
        check(m)

    print()
    print("✅ All Phase-5 modules import successfully")


if __name__ == "__main__":
    main()
