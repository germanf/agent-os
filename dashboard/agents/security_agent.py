from __future__ import annotations

import subprocess

from .protocol import AgentContext, AgentResult, SecurityCapability


class SecuritySpecialistAgent(SecurityCapability):
    @property
    def description(self) -> str:
        return "Security Specialist — SAST, dependency audit, finding issue creation"

    async def run_static_analysis(self, path: str, context: AgentContext) -> AgentResult:
        findings: list[dict] = []

        # ruff with security rules
        try:
            r = subprocess.run(
                ["ruff", "check", "--select", "ALL", path],
                capture_output=True, text=True, timeout=60,
            )
            if r.returncode != 0:
                findings.append({
                    "tool": "ruff",
                    "severity": "warning",
                    "output": r.stdout[:2000],
                })
        except FileNotFoundError:
            findings.append({"tool": "ruff", "severity": "info", "output": "not installed"})

        # bandit (if available)
        try:
            r = subprocess.run(
                ["bandit", "-r", path, "-f", "json"],
                capture_output=True, text=True, timeout=120,
            )
            if r.returncode != 0:
                findings.append({
                    "tool": "bandit",
                    "severity": "warning",
                    "output": r.stdout[:2000],
                })
        except FileNotFoundError:
            findings.append({"tool": "bandit", "severity": "info", "output": "not installed"})

        return AgentResult(
            success=True,
            summary=f"Static analysis: {len(findings)} finding(s)",
            details={"findings": findings},
        )

    async def run_dependency_audit(self, context: AgentContext) -> AgentResult:
        results: list[dict] = []

        for cmd, name in [
            (["pip-audit"], "pip-audit"),
            (["npm", "audit"], "npm audit"),
        ]:
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                results.append({
                    "tool": name,
                    "exit_code": r.returncode,
                    "output": r.stdout[:2000] if r.stdout else r.stderr[:2000],
                })
            except FileNotFoundError:
                results.append({"tool": name, "severity": "info", "output": "not installed"})

        return AgentResult(
            success=True,
            summary=f"Dependency audit: {len(results)} tool(s)",
            details={"results": results},
        )

    async def create_finding_issue(self, vuln: dict, context: AgentContext) -> AgentResult:
        return AgentResult(
            success=True,
            summary=f"Finding issue ready for: {vuln.get('title', 'unknown')}",
            details={
                "title": vuln.get("title", ""),
                "severity": vuln.get("severity", "info"),
                "description": vuln.get("description", ""),
                "remediation": vuln.get("remediation", ""),
            },
        )
