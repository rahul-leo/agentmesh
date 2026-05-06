"""Health-check endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from backend.models.schemas import HealthResponse
from backend.services.run_repository import run_repository

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="agentmesh-backend")


@router.get("/health/storage")
def storage_health() -> dict:
    return run_repository.health()
