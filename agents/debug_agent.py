"""Debug agent that classifies failure logs and points to likely causes."""

from __future__ import annotations

import re
from typing import Any

from .base_agent import AgentFinding, AgentResult, BaseAgent, PipelineTask, llm_think


class DebugAgent(BaseAgent):
    name = "debug-agent"

    ERROR_PATTERNS = {
        "ModuleNotFoundError": "Missing dependency. Try: pip install -r requirements.txt",
        "ImportError": "Import path mismatch. Check if __init__.py is missing in your packages.",
        "AssertionError": "Test failure: The code logic does not match the expected test condition.",
        "TimeoutError": "Execution took too long. Check for infinite loops or slow network calls.",
        "Connection refused": "Service unreachable. Ensure your backend/database is running.",
        "SyntaxError": "Invalid Python syntax. Look for missing colons, brackets, or indentation.",
        "NoSuchElementException": "Selenium: The element was not found. Try using a more robust CSS selector or an XPath.",
        "ElementNotInteractableException": "Selenium: Element is present but hidden. Try scrolling it into view first.",
        "WebDriverException": "Selenium: WebDriver failed to start. Ensure ChromeDriver/GeckoDriver is installed and in PATH.",
        "SessionNotCreatedException": "Selenium: Browser version mismatch. Update your WebDriver to match your Chrome/Firefox version.",
        "vite' is not recognized": "Frontend dependencies are missing or incomplete. Run npm --prefix frontend ci, then npm --prefix frontend run build.",
        "vite: not found": "Frontend dependencies are missing or incomplete. Run npm --prefix frontend ci, then npm --prefix frontend run build.",
        "npm error code EPERM": "Windows blocked npm from replacing a dependency file. Close dev servers/editors, then rerun npm --prefix frontend install or npm --prefix frontend ci.",
        "project_settings_required": "Vercel CLI needs the project linked first. Run vercel pull --yes --environment production or vercel link --yes.",
        "404 NOT_FOUND": "Vercel has not deployed this project/route yet, or the project name does not match the predicted URL.",
        "No project settings found": "The local folder is not linked to Vercel yet. Run vercel link --yes or use the automated deploy script with VERCEL_TOKEN.",
    }

    def run(self, task: PipelineTask, context: dict[str, Any]) -> AgentResult:
        log = task.failure_log or ""
        normalized_log = log.lower()
        build_result = context.get("build-agent")
        
        # 1. Try LLM thinking
        prompt = (
            f"Analyze this software failure log for repository {task.repository}:\n\n"
            f"User requirement: {task.requirement or 'not supplied'}\n"
            f"Target repo files: {task.changed_files}\n"
            f"LOG:\n{log}\n\n"
            "Task: Identify root causes that could block converting the repo into the requested app. "
            "If it's a UI/Selenium error, provide specific Selenium debugging steps. "
            "Return findings as a JSON list of objects with 'title', 'detail', and 'severity' (high/medium/low). "
            "Try to extract file names and line numbers if present."
        )
        if log:
            ai_findings = llm_think(prompt)
            if ai_findings is not None:
                return self.result(
                    "warning" if ai_findings else "passed",
                    f"AI analyzed log and found {len(ai_findings)} likely cause(s) including possible Selenium UI issues." if ai_findings else "AI found no issues.",
                    ai_findings,
                    log_length=len(log),
                )

        # 2. Fallback heuristic
        findings: list[AgentFinding] = []
        matched_patterns: list[str] = []

        for pattern, explanation in self.ERROR_PATTERNS.items():
            if pattern.lower() in normalized_log:
                matched_patterns.append(pattern)
                findings.append(
                    AgentFinding(
                        title=f"Detected {pattern}",
                        detail=explanation,
                        severity="high" if pattern in {"SyntaxError", "AssertionError"} else "medium",
                    )
                )

        for file_ref in self._extract_file_references(log):
            findings.append(
                AgentFinding(
                    title="Referenced file",
                    detail=f"Inspect {file_ref} first; it appears directly in the failure output.",
                    severity="low",
                )
            )

        if any(path.startswith("frontend/") for path in task.changed_files) and (
            "npm" in normalized_log or "vite" in normalized_log
        ):
            findings.append(
                AgentFinding(
                    title="Frontend build path",
                    detail="Run npm --prefix frontend ci and npm --prefix frontend run build from the project root before deploying.",
                    severity="medium",
                )
            )

        if "vercel" in normalized_log:
            findings.append(
                AgentFinding(
                    title="Vercel deployment context",
                    detail="Use scripts/auto_deploy.ps1 or vercel deploy --prod --yes from the agentmesh folder so Vercel reads the correct vercel.json.",
                    severity="medium",
                )
            )

        if not findings and log:
            findings.append(
                AgentFinding(
                    title="Unclassified failure log",
                    detail="The log does not match known patterns. Add a new pattern or route to manual triage.",
                    severity="medium",
                )
            )

        if not log:
            findings.append(
                AgentFinding(
                    title="No failure log supplied",
                    detail="Proceed with proactive debugging: inspect the selected repo files, run the app build, and verify the requirement through UI/API checks.",
                    severity="low",
                )
            )
            if build_result:
                findings.append(
                    AgentFinding(
                        title="Build blueprint available",
                        detail="Use the build-agent output as the source of truth for what must be debugged and verified.",
                        severity="low",
                    )
                )
            return self.result("passed", "No failure log supplied; prepared proactive debugging checks.", findings)

        return self.result(
            "warning",
            f"Analyzed failure log and found {len(findings)} likely cause(s).",
            findings,
            log_length=len(log),
            matched_patterns=matched_patterns,
        )

    def _extract_file_references(self, log: str) -> list[str]:
        references: list[str] = []
        patterns = [
            r"(?P<path>[\w./\\-]+\.(?:jsx|tsx|py|js|ts|json|css|html|yml|yaml))(?::(?P<line>\d+))?",
            r'File "(?P<path>[^"]+)", line (?P<line>\d+)',
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, log):
                path = match.group("path").replace("\\", "/")
                line = match.groupdict().get("line")
                ref = f"{path}:{line}" if line else path
                if ref not in references:
                    references.append(ref)
        return references[:6]
