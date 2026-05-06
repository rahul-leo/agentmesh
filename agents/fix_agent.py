"""Fix agent that proposes safe next patches instead of editing blindly."""

from __future__ import annotations

from typing import Any

from .base_agent import AgentFinding, AgentResult, BaseAgent, PipelineTask, llm_think

class FixAgent(BaseAgent):
    name = "fix-agent"

    def run(self, task: PipelineTask, context: dict[str, Any]) -> AgentResult:
        build_result = context.get("build-agent")
        debug_result = context.get("debug-agent")
        
        # 1. Try to think using LLM
        prompt = (
            f"Task ID: {task.id}\n"
            f"Repository: {task.repository}\n"
            f"Requirement: {task.requirement or 'not supplied'}\n"
            f"Repo files to convert: {task.changed_files}\n"
        )
        if build_result:
            prompt += "Build blueprint from previous agent:\n"
            for f in build_result.findings:
                prompt += f"- {f.title}: {f.detail}\n"
        if debug_result:
            prompt += "Debug Findings from previous agent:\n"
            for f in debug_result.findings:
                prompt += f"- {f.title}: {f.detail}\n"
        prompt += "\nProvide a step-by-step implementation and fix plan that turns the repo into the requested app."
        
        ai_findings = llm_think(prompt)
        if ai_findings is not None:
            status = "passed" if ai_findings else "warning"
            if not ai_findings:
                ai_findings = [AgentFinding("No fix generated", "AI could not determine a fix.", "low")]
            return self.result(status, "AI Generated Fix Plan.", ai_findings)

        # 2. Fallback heuristic
        findings: list[AgentFinding] = []

        if task.changed_files:
            findings.append(
                AgentFinding(
                    title="Files to convert",
                    detail=f"Start implementation with: {', '.join(task.changed_files[:5])}.",
                    severity="medium",
                )
            )

        if task.requirement:
            findings.append(
                AgentFinding(
                    title="Requirement-driven implementation",
                    detail=f"Build toward this outcome first: {task.requirement}",
                    severity="medium",
                )
            )

        if build_result:
            findings.append(
                AgentFinding(
                    title="Follow build blueprint",
                    detail="Apply the build-agent conversion plan before treating remaining issues as bugs.",
                    severity="medium",
                )
            )

        if debug_result:
            for finding in debug_result.findings:
                findings.append(
                    AgentFinding(
                        title=f"Fix plan for {finding.title}",
                        detail=self._recommendation_for(finding.title, finding.detail),
                        severity=finding.severity,
                    )
                )

        if not findings:
            findings.append(
                AgentFinding(
                    title="No automatic fix generated",
                    detail="Add a requirement, target repo files, and any failing output to improve implementation recommendations.",
                    severity="low",
                )
            )
            return self.result("warning", "Generated a conservative fix plan.", findings)

        return self.result("passed", "Generated a conservative fix plan.", findings)

    def _recommendation_for(self, title: str, detail: str) -> str:
        text = f"{title} {detail}".lower()
        if "module" in text or "import" in text:
            return "Check requirements, package names, import paths, and the active virtual environment."
        if "assertion" in text:
            return "Reproduce the failing assertion locally, patch behavior first, and only then update tests."
        if "timeout" in text:
            return "Add explicit timeouts, mocks, or retries around slow external dependencies."
        if "connection" in text:
            return "Verify service startup order, ports, and CI environment variables."
        if "syntax" in text:
            return "Run formatter/linter and inspect the reported line before continuing the pipeline."
        return "Create a minimal failing test, patch the smallest safe area, and rerun CI."
