"""Emit workflow completion as a self-improving skill."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

SKILLS_DIR = Path(__file__).parent / "skills"


def _workflow_to_skill(name: str) -> str:
    return "agent-os-" + name.replace("_", "-")


def _workflow_description(name: str) -> str:
    descs = {
        "system_health": "System health check — verifies system resources are within thresholds",
        "db_backup": "SQLite backup — creates a snapshot of the chat database",
        "job_evict": "Job eviction — removes stale finished jobs from memory (max 200, TTL 1h)",
        "chat_prune": "Chat message pruning — deletes messages older than 7 days",
        "headroom_learn": "Headroom learn — runs scheduled failure mining on the codebase",
        "token_log": "Token usage logging — records daily token consumption per session/project",
        "diagnostics": "Deployment diagnostics — checks frontend build, DB, vault, and Python versions",
        "alerts_prune": "Alert pruning — removes stale alerts from the alerts store",
        "workflow_log_cleanup": "Workflow run log cleanup — removes old workflow_runs entries",
        "scheduler_self_check": "Scheduler self-check — verifies the scheduler loop is ticking",
    }
    return descs.get(name, f"Automated operational workflow: {name}")


def emit_workflow_skill(name: str, result: dict[str, Any] | None) -> str | None:
    """Generate or update a SKILL.md for a completed workflow.

    Returns the path to the skill file if written, None otherwise.
    """
    skill_name = _workflow_to_skill(name)
    skill_dir = SKILLS_DIR / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_path = skill_dir / "SKILL.md"

    content = [
        "---",
        f'name: {skill_name}',
        f'description: {_workflow_description(name)}',
        'version: 1.0.0',
        'author: agent-os',
        'metadata:',
        '  hermes:',
        f'    tags: [workflow, operational, {name}]',
        '    requires_toolsets: [terminal]',
        '---',
        '',
        '## Description',
        '',
        _workflow_description(name) + '.',
        '',
        '## Last Run',
        '',
        f'- Timestamp: {time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())}',
        '- Status: completed',
        f'- Result: {result or {}}',
        '',
        '## How to Invoke',
        '',
        'This workflow runs on a cron schedule managed by the internal scheduler.',
        'To trigger manually:',
        '',
        '```bash',
        f'curl -X POST $BASE_URL/api/scheduler/run -d \'{{"workflow": "{name}"}}\'',
        '```',
    ]

    skill_path.write_text("\n".join(content) + "\n")
    return str(skill_path)
