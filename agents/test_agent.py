"""Test agent for selecting CI checks based on the task shape."""

from __future__ import annotations

from typing import Any

from .base_agent import AgentFinding, AgentResult, BaseAgent, PipelineTask, llm_think

class TestAgent(BaseAgent):
    name = "test-agent"

    def run(self, task: PipelineTask, context: dict[str, Any]) -> AgentResult:
        files = task.changed_files or []
        
        # 1. Try LLM thinking
        prompt = (
            f"Changed files: {files}\n"
            f"Repository: {task.repository}\n"
            f"Requirement: {task.requirement or 'not supplied'}\n"
            "What testing commands should verify that the repo was converted into the requested app? "
            "You MUST include end-to-end UI tests using Selenium (https://www.selenium.dev/) as part of your plan."
        )
        ai_findings = llm_think(prompt)
        if ai_findings is not None:
            return self.result("passed", "AI selected CI checks including Selenium UI tests.", ai_findings)

        # 2. Fallback heuristic
        commands = [
            "python -m pytest",
            "npm --prefix frontend run build",
            "pip install selenium",
            "python -m pytest tests/e2e/ --driver Chrome" # Selenium fallback command
        ]

        if any(path.endswith(".py") for path in files):
            commands.insert(0, "python -m compileall .")
        if any(path.startswith("frontend/") for path in files):
            commands.append("cd frontend && npm test -- --run")
        if any(path.startswith("docker/") or path.endswith("Dockerfile") for path in files):
            commands.append("docker compose -f docker/docker-compose.yml config")

        findings = [
            AgentFinding(title="Recommended test command", detail=command, severity="low")
            for command in commands
        ]

        findings.append(
            AgentFinding(
                title="Requirement verification",
                detail=task.requirement or "Verify the delivered app matches the user's requested outcome.",
                severity="medium",
            )
        )

        return self.result("passed", "Selected conversion, CI, and Selenium checks.", findings, commands=commands)
