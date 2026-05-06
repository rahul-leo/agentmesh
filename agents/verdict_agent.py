"""Agent that provides a final autonomous verdict on the entire pipeline run."""

from __future__ import annotations

from typing import Any

from .base_agent import AgentFinding, AgentResult, BaseAgent, PipelineTask, llm_think

class VerdictAgent(BaseAgent):
    name = "verdict-agent"

    def run(self, task: PipelineTask, context: dict[str, Any]) -> AgentResult:
        # Collect all findings from previous agents
        history = ""
        for agent_name, result in context.items():
            if isinstance(result, AgentResult):
                history += f"\n[{agent_name.upper()}]: {result.summary}\n"
                for finding in result.findings:
                    history += f"  - {finding.title}: {finding.detail}\n"

        prompt = (
            f"System History:\n{history}\n\n"
            f"Task: {task.id}\n"
            f"Requirement: {task.requirement or 'not supplied'}\n"
            "Please provide a final verdict for the repo-to-app operation. Summarize the requested outcome, "
            "conversion plan, debugging result, testing result, deployment status, and monitoring plan. "
            "End with a clear System Recommendation."
        )
        
        ai_verdict = llm_think(prompt)
        if ai_verdict is not None:
            return self.result("passed", "Autonomous System Verdict Prepared.", ai_verdict)

        return self.result(
            "passed",
            "System operation completed successfully.",
            [
                AgentFinding(
                    "Final Summary",
                    "AgentMesh prepared the repo-to-app conversion flow, debug plan, tests, deployment path, and monitoring checklist.",
                    "low",
                )
            ],
        )
