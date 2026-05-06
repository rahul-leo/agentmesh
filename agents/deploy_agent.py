"""Deploy agent that evaluates release readiness."""

from __future__ import annotations

import httpx
from typing import Any
from urllib.parse import quote, urlparse

from .base_agent import AgentFinding, AgentResult, BaseAgent, PipelineTask, llm_think


def _clean_repository_url(repository: str) -> str:
    repo_url = repository.strip().rstrip("/")
    if "/blob/" in repo_url:
        return repo_url.split("/blob/")[0]
    if "/tree/" in repo_url:
        return repo_url.split("/tree/")[0]
    return repo_url


def _repo_slug(repository: str) -> str:
    repo_url = _clean_repository_url(repository)
    path = urlparse(repo_url).path if repo_url.startswith(("http://", "https://")) else repo_url
    return path.rstrip("/").split("/")[-1].replace(".git", "") or "agentmesh"


class DeployAgent(BaseAgent):
    name = "deploy-agent"

    def run(self, task: PipelineTask, context: dict[str, Any]) -> AgentResult:
        risk_score = context.get("risk_score", 0.0)

        repo_url = _clean_repository_url(task.repository)
        repo_name = _repo_slug(repo_url)
        build_result = context.get("build-agent")
        live_link = f"https://{repo_name}.vercel.app"
        render_live_link = f"https://{repo_name}.onrender.com"
        one_click_deploy = (
            "https://vercel.com/new/clone"
            f"?repository-url={quote(repo_url, safe='')}"
            f"&project-name={quote(repo_name, safe='')}"
        )
        render_deploy_url = (
            "https://render.com/deploy"
            f"?repo={quote(repo_url, safe='')}"
        )
        public_launch_command = (
            '$env:VERCEL_TOKEN = "<your-vercel-token>"\n'
            f'.\\scripts\\auto_deploy.ps1 -GitHubRepo "{repo_url}" '
            f'-VercelProjectName "{repo_name}" -GitHubVisibility public'
        )
        render_launch_command = (
            "Open https://dashboard.render.com/ and create a new Blueprint or Web Service from this GitHub repo.\n"
            "For FastAPI Web Service use:\n"
            "Build Command: pip install -r requirements.txt\n"
            "Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT\n"
            "For frontend Static Site use:\n"
            "Build Command: npm --prefix frontend install && npm --prefix frontend run build\n"
            "Publish Directory: frontend/dist"
        )
        clean_repo = repo_url if repo_url.startswith("http") else task.repository

        is_live = False
        is_render_live = False
        try:
            response = httpx.get(live_link, timeout=5.0, follow_redirects=True)
            if response.status_code < 400:
                is_live = True
        except Exception:
            is_live = False
        try:
            response = httpx.get(render_live_link, timeout=5.0, follow_redirects=True)
            if response.status_code < 400:
                is_render_live = True
        except Exception:
            is_render_live = False

        # 1. Try LLM thinking
        prompt = (
            f"Environment: {task.environment}\n"
            f"Commit: {task.commit_sha or 'NOT PROVIDED'}\n"
            f"Repository Root: {clean_repo}\n"
            f"Project Name: {repo_name}\n"
            f"Requirement: {task.requirement or 'not supplied'}\n"
            f"Build Agent Summary: {build_result.summary if isinstance(build_result, AgentResult) else 'not available'}\n"
            f"Risk Score: {risk_score}\n"
            f"Is Live (verified): {is_live}\n"
            "Evaluate deployment readiness for a GitHub repository deployed by Vercel or Render. "
            "Propose exact production deploy commands for both options. "
            f"Use this Vercel public launch URL when setup is pending: {one_click_deploy}. "
            f"Use this Render public deploy URL when setup is pending: {render_deploy_url}. "
            f"Use this Vercel automated public launch command: {public_launch_command}. "
            f"Use this Render launch setup: {render_launch_command}. "
            f"The predicted live URL after a successful deploy is {live_link}. "
            f"The predicted Render URL after a successful deploy is {render_live_link}. "
            "If the commit is missing, suggest running `git rev-parse HEAD` to get it. "
            "Return findings as JSON list."
        )
        ai_findings = llm_think(prompt)
        
        if ai_findings is not None:
            has_high_severity = any(f.severity == "high" for f in ai_findings)
            
            summary = "AI deployment analysis complete. Deployment is ready but PENDING execution."
            if is_live:
                summary = "AI deployment analysis complete. Deployment is VERIFIED and LIVE."
                ai_findings.append(AgentFinding(
                    title="Live Link: VERIFIED",
                    detail=f"The deployment at {live_link} is already online and responding correctly.",
                    severity="low"
                ))
            else:
                ai_findings.append(AgentFinding(
                    title="Current Link Status: PENDING",
                    detail="The live link will show a 404 NOT_FOUND until you run the 'vercel --prod' command in your terminal. This is expected behavior for the first deployment.",
                    severity="medium"
                ))

            return self.result(
                "warning" if has_high_severity else "passed", 
                summary, 
                ai_findings, 
                risk_score=risk_score,
                deployment_url=live_link,
                one_click_url=one_click_deploy,
                public_launch_command=public_launch_command,
                render_deployment_url=render_live_link,
                render_deploy_url=render_deploy_url,
                render_launch_command=render_launch_command,
                normalized_repository=repo_url,
                is_live=is_live,
                is_render_live=is_render_live,
            )

        # 2. Fallback heuristic
        findings: list[AgentFinding] = []
        
        if is_live:
            findings.append(AgentFinding(
                title="Live Link: VERIFIED",
                detail=f"The deployment at {live_link} is reachable.",
                severity="low"
            ))
        else:
            findings.append(AgentFinding(
                title="Live Link Status",
                detail="The predicted Vercel URL is not responding yet. This is normal until the GitHub repository is imported into Vercel or deployed with the Vercel CLI.",
                severity="medium"
            ))

        if "github.com" not in repo_url:
            findings.append(
                AgentFinding(
                    title="GitHub Repository Required",
                    detail="Push this project to GitHub first, then import that repository in Vercel.",
                    severity="medium",
                )
            )

        if task.environment == "production" and not task.commit_sha:
            findings.append(
                AgentFinding(
                    title="Missing commit SHA",
                    detail="Production deploys should pin an immutable commit SHA before Vercel deployment.",
                    severity="high",
                )
            )

        if risk_score >= 0.7:
            findings.append(
                AgentFinding(
                    title="High deployment risk",
                    detail="Risk predictor recommends holding Vercel deployment until failures are resolved.",
                    severity="high",
                )
            )

        if not any(f.severity == "high" for f in findings):
            if isinstance(build_result, AgentResult):
                findings.append(
                    AgentFinding(
                        title="Deploy Built Outcome",
                        detail=f"Deploy after this build stage passes: {build_result.summary}",
                        severity="low",
                    )
                )
            findings.append(
                AgentFinding(
                    title="Public Launch Process",
                    detail="Open either the Vercel public launch URL or Render dashboard after debug, fix, test, and build stages are complete. The agent normalizes GitHub file links to the repository root before deploying.",
                    severity="low",
                )
            )
            findings.append(
                AgentFinding(
                    title="Vercel Public Launch URL",
                    detail=one_click_deploy,
                    severity="low",
                )
            )
            findings.append(
                AgentFinding(
                    title="Render Public Deploy URL",
                    detail=render_deploy_url,
                    severity="low",
                )
            )
            findings.append(
                AgentFinding(
                    title="Vercel Automated Public Launch Command",
                    detail=public_launch_command,
                    severity="low",
                )
            )
            findings.append(
                AgentFinding(
                    title="Render Deploy Setup",
                    detail=render_launch_command,
                    severity="low",
                )
            )
            findings.append(
                AgentFinding(
                    title="Vercel CLI Production Deploy",
                    detail="vercel deploy --prod --yes",
                    severity="low",
                )
            )
            findings.append(
                AgentFinding(
                    title="Predicted Live Link",
                    detail=live_link,
                    severity="low",
                )
            )
            return self.result(
                "passed", 
                "Deployment checks passed; " + ("verified live." if is_live else "ready to deploy to Vercel."), 
                findings, 
                risk_score=risk_score,
                deployment_url=live_link,
                one_click_url=one_click_deploy,
                public_launch_command=public_launch_command,
                render_deployment_url=render_live_link,
                render_deploy_url=render_deploy_url,
                render_launch_command=render_launch_command,
                normalized_repository=repo_url,
                is_live=is_live,
                is_render_live=is_render_live,
            )

        return self.result("failed", "Vercel deployment is blocked by readiness checks.", findings, risk_score=risk_score)
