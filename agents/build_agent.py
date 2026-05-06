"""Build agent that turns repository files and user requirements into an app plan."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any

from .base_agent import AgentFinding, AgentResult, BaseAgent, PipelineTask, llm_think


class BuildAgent(BaseAgent):
    name = "build-agent"

    def run(self, task: PipelineTask, context: dict[str, Any]) -> AgentResult:
        files = task.changed_files or []
        requirement = task.requirement.strip()
        previous_summary = self._previous_agent_summary(context)

        if not task.repository:
            return self.result(
                "failed",
                "A GitHub repository is required before AgentMesh can build an app.",
                [AgentFinding("Missing repository", "Provide the GitHub link that contains the source files.", "high")],
            )

        if not requirement:
            return self.result(
                "warning",
                "No product requirement was supplied, so AgentMesh prepared a generic app conversion plan.",
                [
                    AgentFinding(
                        "Missing requirement",
                        "Describe what the repo should become, for example: portfolio website, dashboard, API app, game, or landing page.",
                        "medium",
                    )
                ],
                target_files=files,
            )

        prompt = (
            f"Repository: {task.repository}\n"
            f"Branch: {task.branch}\n"
            f"Target files in repo: {files}\n"
            f"User requirement: {requirement}\n\n"
            f"Previous debug/fix/test context:\n{previous_summary}\n\n"
            "You are the BuildAgent. After debug, fix, and test planning, decide how to convert these repo files into the requested app, website, tool, or API before deployment. "
            "Return JSON findings that include target output, file changes, framework/build commands, and acceptance criteria."
        )
        ai_findings = llm_think(prompt)
        if ai_findings is not None:
            return self.result(
                "passed",
                "Prepared the app conversion blueprint from the repository files and requirement.",
                ai_findings,
                target_files=files,
                requirement=requirement,
                app_type=self._infer_app_type(requirement, files),
            )

        app_type = self._infer_app_type(requirement, files)
        findings = [
            AgentFinding(
                "Target outcome",
                f"Convert the selected repository files into a deployable {app_type}.",
                "low",
            ),
            AgentFinding(
                "Source files to transform",
                ", ".join(files[:8]) if files else "No specific files supplied; inspect the repository root and app entrypoints first.",
                "medium" if not files else "low",
            ),
            AgentFinding(
                "Requirement",
                requirement,
                "low",
            ),
            AgentFinding(
                "Implementation path",
                self._implementation_path(app_type, files, previous_summary),
                "medium",
            ),
            AgentFinding(
                "Acceptance criteria",
                "The generated app runs locally, has a production build, routes correctly on Vercel, and matches the stated requirement.",
                "low",
            ),
        ]
        return self.result(
            "passed",
            "Prepared the app conversion blueprint from the repository files and requirement.",
            findings,
            target_files=files,
            requirement=requirement,
            app_type=app_type,
        )

    def _infer_app_type(self, requirement: str, files: list[str]) -> str:
        text = f"{requirement} {' '.join(files)}".lower()
        if any(word in text for word in ("portfolio", "landing", "website", "html", "css")):
            return "website"
        if any(word in text for word in ("dashboard", "admin", "crm", "analytics")):
            return "dashboard app"
        if any(word in text for word in ("game", "canvas", "play")):
            return "interactive game"
        if any(word in text for word in ("api", "backend", "fastapi", "server")):
            return "API-backed app"
        return "web app"

    def _implementation_path(self, app_type: str, files: list[str], previous_summary: str = "") -> str:
        extensions = {PurePosixPath(path.replace("\\", "/")).suffix.lower() for path in files}
        if ".html" in extensions and not ({".jsx", ".tsx", ".js", ".ts"} & extensions):
            return "After debug and test checks pass, use the HTML/CSS/JS files as the app base, add missing routing/assets, then publish as a static Vercel site."
        if {".jsx", ".tsx", ".js", ".ts"} & extensions:
            return "After fixes are planned, create or update the Vite/React app surface, wire the selected files into a production entrypoint, then run npm build checks."
        if ".py" in extensions:
            return "After backend tests are selected, expose the Python logic through FastAPI routes and pair it with a frontend page that satisfies the requirement."
        return f"Inspect the repository structure, choose the simplest deployable {app_type} shape, then add build and test commands."

    def _previous_agent_summary(self, context: dict[str, Any]) -> str:
        lines: list[str] = []
        for agent_name in ("debug-agent", "fix-agent", "autofix-agent", "test-agent"):
            result = context.get(agent_name)
            if isinstance(result, AgentResult):
                lines.append(f"{agent_name}: {result.summary}")
        return "\n".join(lines) or "No previous agent context supplied."
