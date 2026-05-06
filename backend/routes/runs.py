"""Pipeline run endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from backend.models.schemas import RunHistoryResponse, RunRequest, RunResponse
from backend.services.pipeline_service import pipeline_service

router = APIRouter(prefix="/api", tags=["runs"])


@router.post("/runs", response_model=RunResponse)
def create_run(request: RunRequest) -> dict:
    return pipeline_service.run_pipeline(request)


@router.get("/runs", response_model=RunHistoryResponse)
def list_runs(limit: int = Query(default=20, ge=1, le=100)) -> dict:
    return {"runs": pipeline_service.list_runs(limit=limit)}


@router.get("/runs/{run_id}")
def get_run(run_id: str) -> dict:
    run = pipeline_service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run
