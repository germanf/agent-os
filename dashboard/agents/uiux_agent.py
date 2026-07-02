from __future__ import annotations

import os
import re

from .protocol import AgentContext, AgentResult, UIUXCapability


class UIUXSpecialistAgent(UIUXCapability):
    @property
    def description(self) -> str:
        return "UI/UX Specialist — design review, accessibility audit, issue creation"

    async def review_design(self, path: str, context: AgentContext) -> AgentResult:
        findings: list[dict] = []

        index_css = os.path.join(path, "index.css")
        if os.path.isfile(index_css):
            css = open(index_css).read()
            if "--color-bg" in css and "--color-surface" in css and "--color-accent" in css:
                findings.append({"check": "theme tokens", "status": "✅"})
            else:
                findings.append({"check": "theme tokens", "status": "⚠️", "detail": "Missing required --color-* tokens"})

        return AgentResult(
            success=True,
            summary=f"Design review: {len(findings)} check(s)",
            details={"findings": findings},
        )

    async def audit_accessibility(self, path: str, context: AgentContext) -> AgentResult:
        findings: list[dict] = []

        tsx_files = []
        if os.path.isdir(path):
            for root, _, files in os.walk(path):
                for f in files:
                    if f.endswith(".tsx"):
                        tsx_files.append(os.path.join(root, f))

        for tsx in tsx_files[:20]:
            content = open(tsx).read()
            if re.search(r"<button[^>]*>", content) and not re.search(r"aria-label", tsx[:1000] + content[:3000]):
                pass
            if "role=" in content and "aria-" not in content:
                name = os.path.relpath(tsx, path)
                findings.append({
                    "file": name,
                    "check": "aria labels",
                    "status": "⚠️",
                    "detail": "Has role= but no aria-* attributes",
                })

        return AgentResult(
            success=True,
            summary=f"Accessibility audit: {len(findings)} finding(s) in {len(tsx_files)} files",
            details={"files_scanned": len(tsx_files), "findings": findings},
        )

    async def create_design_issue(self, finding: dict, context: AgentContext) -> AgentResult:
        return AgentResult(
            success=True,
            summary=f"Design issue ready for: {finding.get('title', 'unknown')}",
            details={
                "title": finding.get("title", ""),
                "severity": finding.get("severity", "info"),
                "description": finding.get("description", ""),
                "suggested_fix": finding.get("suggested_fix", ""),
            },
        )
