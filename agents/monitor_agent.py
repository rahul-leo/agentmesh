"""Monitor agent that defines post-deploy health signals."""

from __future__ import annotations

from typing import Any

from .base_agent import AgentFinding, AgentResult, BaseAgent, PipelineTask, llm_think

class MonitorAgent(BaseAgent):
    name = "monitor-agent"

    def run(self, task: PipelineTask, context: dict[str, Any]) -> AgentResult:
        # 1. Try LLM thinking
        prompt = (
            f"Changed files: {task.changed_files}\n"
            f"Repository: {task.repository}\n"
            f"Requirement: {task.requirement or 'not supplied'}\n"
            "Suggest post-deploy metrics that prove the generated app/website/tool remains healthy. "
            "You MUST include Selenium (https://www.selenium.dev/) synthetic UI monitoring tests as part of the checklist."
        )
        ai_findings = llm_think(prompt)
        if ai_findings is not None:
            return self.result("passed", "AI prepared post-deploy monitoring checklist including Selenium.", ai_findings)

        # 2. Fallback heuristic
        signals = [
            "HTTP 5xx rate",
            "p95 latency",
            "error logs",
            "CPU and memory usage",
            "deployment rollback events",
            "requirement acceptance checks",
            "Selenium Automated Synthetic UI Test Results",
        ]
        findings = [
            AgentFinding(title="Monitor signal", detail=signal, severity="low")
            for signal in signals
        ]
        return self.result("passed", "Prepared post-deploy monitoring checklist with Selenium.", findings, signals=signals)
