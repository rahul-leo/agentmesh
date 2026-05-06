"""Shared primitives for all AgentMesh agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

AgentStatus = Literal["pending", "running", "passed", "failed", "warning"]


@dataclass
class AgentFinding:
    """A structured observation produced by an agent."""

    title: str
    detail: str
    severity: Literal["low", "medium", "high"] = "low"


@dataclass
class AgentResult:
    """A result emitted by one pipeline stage."""

    agent: str
    status: AgentStatus
    summary: str
    findings: list[AgentFinding] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    completed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class PipelineTask:
    """Input passed through the debugging and CI/CD mesh."""

    repository: str
    branch: str = "main"
    commit_sha: str | None = None
    requirement: str = ""
    failure_log: str = ""
    changed_files: list[str] = field(default_factory=list)
    environment: Literal["local", "staging", "production"] = "local"
    id: str = field(default_factory=lambda: str(uuid4()))


class BaseAgent:
    """Base class that gives every agent a consistent interface."""

    name = "base-agent"

    def run(self, task: PipelineTask, context: dict[str, Any]) -> AgentResult:
        raise NotImplementedError

    def result(
        self,
        status: AgentStatus,
        summary: str,
        findings: list[AgentFinding] | None = None,
        **metadata: Any,
    ) -> AgentResult:
        return AgentResult(
            agent=self.name,
            status=status,
            summary=summary,
            findings=findings or [],
            metadata=metadata,
        )

import os
import json
import httpx

def llm_think(prompt: str) -> list[AgentFinding] | None:
    """Uses Gemini API to think and return findings. Returns None if no key or error."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        return None
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {
            "parts": [{"text": "You are an expert AI agent inside AgentMesh. Analyze the context and return your findings ONLY as a JSON array of objects. Each object must have 'title' (string), 'detail' (string), and 'severity' (string: 'low', 'medium', or 'high'). Return valid JSON only, without markdown formatting."}]
        },
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    try:
        response = httpx.post(url, json=payload, timeout=20.0)
        response.raise_for_status()
        data = response.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        parsed = json.loads(text)
        return [AgentFinding(**item) for item in parsed]
    except Exception as e:
        print(f"LLM Error: {e}")
        return None
