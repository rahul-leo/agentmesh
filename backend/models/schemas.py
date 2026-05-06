"""API schemas for AgentMesh."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RunRequest(BaseModel):
    repository: str = Field(..., examples=["https://github.com/example/project"])
    branch: str = "main"
    commit_sha: str | None = None
    requirement: str = Field(
        default="",
        examples=["Convert the selected repo files into a responsive portfolio website and deploy it."],
    )
    failure_log: str = ""
    changed_files: list[str] = Field(default_factory=list)
    environment: Literal["local", "staging", "production"] = "local"


class HealthResponse(BaseModel):
    status: str
    service: str


class RunResponse(BaseModel):
    task: dict
    status: str
    risk: dict
    results: list[dict]
    id: str | None = None
    persisted: bool = False
    storage_error: str | None = None


class RunHistoryResponse(BaseModel):
    runs: list[dict]
