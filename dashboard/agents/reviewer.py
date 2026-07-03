from __future__ import annotations

import os
import subprocess

from .protocol import AgentContext, AgentResult, ReviewerCapability


class TechLeadAgent(ReviewerCapability):
    @property
    def description(self) -> str:
        return "Automated Tech Lead — code review, validation, and triage"

    async def review_pr(self, pr_details: dict, context: AgentContext) -> AgentResult:
        review_parts: list[str] = []

        # 1. Run validate-workflow.sh
        script = os.path.join(context.project_root, "scripts", "validate-workflow.sh")
        if os.path.exists(script):
            try:
                result = subprocess.run(
                    ["bash", script],
                    capture_output=True, text=True, timeout=120,
                )
                review_parts.append(f"## Validation\n\n```\n{result.stdout}\n{result.stderr}\n```")
                review_parts.append(f"**Exit code:** {result.returncode}")
            except (subprocess.TimeoutExpired, OSError) as exc:
                review_parts.append(f"## Validation\n\nFailed to run: {exc}")

        # 2. Check branch naming
        branch = pr_details.get("branch", "")
        if branch.startswith("feature/") or branch.startswith("fix/"):
            review_parts.append(f"**Branch:** {branch} ✅")
        else:
            review_parts.append(f"**Branch:** {branch} ❌ (must be feature/* or fix/*)")

        # 3. Check PR references an issue
        body = pr_details.get("body", "")
        if "Related to #" in body:
            review_parts.append("**Issue reference:** ✅")
        else:
            review_parts.append("**Issue reference:** ❌ (missing 'Related to #N')")

        summary = "\n\n".join(review_parts)
        return AgentResult(success=True, summary="Review complete", details={"review": summary})

    async def check_standards(self, path: str, context: AgentContext) -> AgentResult:
        checks: list[str] = []

        # ruff
        try:
            r = subprocess.run(
                ["ruff", "check", path], capture_output=True, text=True, timeout=60,
            )
            checks.append(f"ruff: {'✅' if r.returncode == 0 else '❌'}")
            if r.stdout:
                checks.append(f"```\n{r.stdout[:2000]}\n```")
        except FileNotFoundError:
            checks.append("ruff: ⚠️ not installed")

        # py_compile
        main_py = os.path.join(path, "main.py") if os.path.isdir(path) else path
        if os.path.isfile(main_py) or os.path.isdir(os.path.join(path, "main.py")):
            try:
                r = subprocess.run(
                    ["python3", "-m", "py_compile", "dashboard/main.py"],
                    capture_output=True, text=True, timeout=30, cwd=path,
                )
                checks.append(f"py_compile: {'✅' if r.returncode == 0 else '❌'}")
            except (subprocess.TimeoutExpired, OSError) as e:
                checks.append(f"py_compile: ⚠️ {e}")

        return AgentResult(
            success=True,
            summary="Standards check complete",
            details={"checks": "\n".join(checks)},
        )
