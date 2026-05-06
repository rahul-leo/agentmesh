from agents.base_agent import PipelineTask
from agents.debug_agent import DebugAgent
from agents.deploy_agent import DeployAgent
from agents.manager_agent import ManagerAgent
from ml.predict import predict_failure_risk


def test_manager_runs_all_agents_for_failure_log():
    task = PipelineTask(
        repository="local-project",
        branch="main",
        failure_log="AssertionError: expected deployment gate to pass",
        changed_files=["agents/debug_agent.py"],
        environment="staging",
    )

    result = ManagerAgent().run(task)

    assert result["task"]["repository"] == "local-project"
    assert result["risk"]["risk_label"] == "medium"
    assert [item["agent"] for item in result["results"]] == [
        "debug-agent",
        "fix-agent",
        "autofix-agent",
        "test-agent",
        "build-agent",
        "deploy-agent",
        "monitor-agent",
        "verdict-agent",
    ]


def test_production_without_commit_blocks_deploy():
    task = PipelineTask(
        repository="local-project",
        environment="production",
        failure_log="SyntaxError: invalid syntax",
        changed_files=["backend/main.py"],
    )

    result = ManagerAgent().run(task)
    deploy_result = next(item for item in result["results"] if item["agent"] == "deploy-agent")

    assert result["status"] == "failed"
    assert deploy_result["status"] == "failed"
    assert any(finding["title"] == "Missing commit SHA" for finding in deploy_result["findings"])


def test_risk_predictor_handles_low_risk_local_task():
    risk = predict_failure_risk(
        failure_log="",
        changed_files=["docs/architecture.md"],
        environment="local",
    )

    assert risk["risk_score"] == 0.1
    assert risk["risk_label"] == "low"


def test_debug_agent_identifies_vercel_frontend_failures():
    task = PipelineTask(
        repository="https://github.com/example/agentmesh",
        failure_log="'vite' is not recognized as an internal or external command\nnpm error code EPERM\nfrontend/src/main.jsx:12",
        changed_files=["frontend/src/main.jsx"],
    )

    result = DebugAgent().run(task, {})

    assert result.status == "warning"
    assert "vite' is not recognized" in result.metadata["matched_patterns"]
    assert any(finding.title == "Frontend build path" for finding in result.findings)
    assert any("frontend/src/main.jsx:12" in finding.detail for finding in result.findings)


def test_deploy_agent_normalizes_github_file_url_for_public_launch():
    task = PipelineTask(
        repository="https://github.com/rahul-leo/nm-git/blob/main2/test.html",
        environment="staging",
    )

    result = DeployAgent().run(task, {"risk_score": 0.1})

    assert result.metadata["normalized_repository"] == "https://github.com/rahul-leo/nm-git"
    assert "repository-url=https%3A%2F%2Fgithub.com%2Frahul-leo%2Fnm-git" in result.metadata["one_click_url"]
    assert result.metadata["render_deploy_url"].endswith("repo=https%3A%2F%2Fgithub.com%2Frahul-leo%2Fnm-git")
    assert any(finding.title == "Vercel Public Launch URL" for finding in result.findings)
    assert any(finding.title == "Render Public Deploy URL" for finding in result.findings)
    assert any(finding.title == "Vercel Automated Public Launch Command" for finding in result.findings)
    assert any(finding.title == "Render Deploy Setup" for finding in result.findings)
