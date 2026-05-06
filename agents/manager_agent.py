"""Coordinator for the autonomous debugging and CI/CD pipeline."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ml.predict import predict_failure_risk

from .base_agent import AgentResult, PipelineTask
from .build_agent import BuildAgent
from .debug_agent import DebugAgent
from .deploy_agent import DeployAgent
from .fix_agent import FixAgent
from .autofix_agent import AutoFixAgent
from .monitor_agent import MonitorAgent
from .test_agent import TestAgent
from .verdict_agent import VerdictAgent


class ManagerAgent:
    """Runs specialized agents in a deterministic, auditable order."""

    def __init__(self) -> None:
        self.agents = [
            DebugAgent(), 
            FixAgent(), 
            AutoFixAgent(), 
            TestAgent(), 
            BuildAgent(),
            DeployAgent(), 
            MonitorAgent(),
            VerdictAgent()
        ]

    def run(self, task: PipelineTask) -> dict[str, Any]:
        context: dict[str, Any] = {}
        risk = predict_failure_risk(
            failure_log=task.failure_log,
            changed_files=task.changed_files,
            environment=task.environment,
        )
        context["risk_score"] = risk["risk_score"]
        context["risk_label"] = risk["risk_label"]

        results: list[AgentResult] = []
        for agent in self.agents:
            result = agent.run(task, context)
            results.append(result)
            context[result.agent] = result

        status = "failed" if any(result.status == "failed" for result in results) else "warning"
        if all(result.status == "passed" for result in results):
            status = "passed"

        return {
            "task": asdict(task),
            "status": status,
            "risk": risk,
            "results": [asdict(result) for result in results],
        }
