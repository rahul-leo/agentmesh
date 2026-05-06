"""Service wrapper around the manager agent."""

from __future__ import annotations

from agents.base_agent import PipelineTask
from agents.manager_agent import ManagerAgent
from backend.models.schemas import RunRequest
from backend.services.run_repository import run_repository


class PipelineService:
    def __init__(self) -> None:
        self.manager = ManagerAgent()

    def run_pipeline(self, request: RunRequest) -> dict:
        task = PipelineTask(**request.model_dump())
        result = self.manager.run(task)
        stored_id, error = run_repository.save_run(result)
        result["id"] = stored_id
        result["persisted"] = stored_id is not None
        result["storage_error"] = error
        return result

    def list_runs(self, limit: int = 20) -> list[dict]:
        return run_repository.list_runs(limit=limit)

    def get_run(self, run_id: str) -> dict | None:
        return run_repository.get_run(run_id)


pipeline_service = PipelineService()
