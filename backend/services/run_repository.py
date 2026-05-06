"""Firebase Firestore persistence for pipeline runs."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import httpx


class FirebaseRunRepository:
    """Stores and retrieves AgentMesh runs from Firebase Firestore, with an in-memory fallback."""

    def __init__(self) -> None:
        self.project_id = os.getenv("FIREBASE_PROJECT_ID", "")
        self.api_key = os.getenv("FIREBASE_API_KEY", "")
        self.collection_name = os.getenv("FIREBASE_RUNS_COLLECTION", "runs")
        self.database_id = os.getenv("FIREBASE_DATABASE_ID", "(default)")
        self.timeout = float(os.getenv("FIREBASE_TIMEOUT_SECONDS", "6"))
        self.base_url = (
            f"https://firestore.googleapis.com/v1/projects/{self.project_id}"
            f"/databases/{self.database_id}/documents"
        )
        self._memory_runs: dict[str, dict[str, Any]] = {}
        # Use local memory by default so public clones run without private Firebase credentials.
        self._use_memory = (
            os.getenv("FIREBASE_USE_MEMORY", "false").lower() == "true"
            or not self.project_id
            or not self.api_key
        )

    def save_run(self, run: dict[str, Any]) -> tuple[str | None, str | None]:
        """Persist a run and return `(id, error)`."""
        document_id = run["task"]["id"]
        document = {
            **run,
            "run_id": document_id,
            "created_at": datetime.now(timezone.utc),
        }

        if self._use_memory:
            self._memory_runs[document_id] = document
            return document_id, None

        try:
            response = httpx.post(
                f"{self.base_url}/{self.collection_name}",
                params={"key": self.api_key, "documentId": document_id},
                json={"fields": self._to_firestore_fields(document)},
                timeout=self.timeout,
            )

            if response.status_code == 409:
                response = httpx.patch(
                    f"{self.base_url}/{self.collection_name}/{quote(document_id, safe='')}",
                    params={"key": self.api_key},
                    json={"fields": self._to_firestore_fields(document)},
                    timeout=self.timeout,
                )

            self._raise_for_status(response)
            return document_id, None
        except (httpx.HTTPError, RuntimeError) as exc:
            self._use_memory = True
            self._memory_runs[document_id] = document
            return document_id, str(exc)

    def list_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        if self._use_memory:
            sorted_runs = sorted(self._memory_runs.values(), key=lambda x: x["created_at"], reverse=True)
            return [self._from_memory(r, include_results=False) for r in sorted_runs[:limit]]

        try:
            response = httpx.get(
                f"{self.base_url}/{self.collection_name}",
                params={
                    "key": self.api_key,
                    "pageSize": limit,
                    "orderBy": "created_at desc",
                },
                timeout=self.timeout,
            )
            self._raise_for_status(response)
            documents = response.json().get("documents", [])
            return [self._from_document(document, include_results=False) for document in documents]
        except (httpx.HTTPError, RuntimeError):
            self._use_memory = True
            sorted_runs = sorted(self._memory_runs.values(), key=lambda x: x["created_at"], reverse=True)
            return [self._from_memory(r, include_results=False) for r in sorted_runs[:limit]]

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        if self._use_memory:
            r = self._memory_runs.get(run_id)
            return self._from_memory(r) if r else None

        try:
            response = httpx.get(
                f"{self.base_url}/{self.collection_name}/{quote(run_id, safe='')}",
                params={"key": self.api_key},
                timeout=self.timeout,
            )
            if response.status_code == 404:
                return None
            self._raise_for_status(response)
            return self._from_document(response.json())
        except (httpx.HTTPError, RuntimeError):
            self._use_memory = True
            r = self._memory_runs.get(run_id)
            return self._from_memory(r) if r else None

    def health(self) -> dict[str, str | bool]:
        if self._use_memory:
            return {
                "connected": True,
                "provider": "in-memory (fallback)",
                "project_id": "local",
                "collection": self.collection_name,
            }

        try:
            response = httpx.get(
                f"{self.base_url}/{self.collection_name}",
                params={"key": self.api_key, "pageSize": 1},
                timeout=self.timeout,
            )
            self._raise_for_status(response)
            return {
                "connected": True,
                "provider": "firebase",
                "project_id": self.project_id,
                "collection": self.collection_name,
            }
        except (httpx.HTTPError, RuntimeError) as exc:
            self._use_memory = True
            return {
                "connected": True,
                "provider": "in-memory (fallback)",
                "project_id": "local",
                "collection": self.collection_name,
                "error_bypassed": str(exc),
            }

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.is_success:
            return
        raise RuntimeError(f"Firebase returned {response.status_code}: {response.text}")

    def _from_document(self, document: dict[str, Any], include_results: bool = True) -> dict[str, Any]:
        value = self._from_firestore_fields(document.get("fields", {}))
        value.setdefault("id", document.get("name", "").rsplit("/", 1)[-1])
        if not include_results:
            value.pop("results", None)
        return value

    def _from_memory(self, document: dict[str, Any], include_results: bool = True) -> dict[str, Any]:
        if not document:
            return document
        value = document.copy()
        value["id"] = value.get("run_id")
        if not include_results:
            value.pop("results", None)
        # convert timestamp to string so it's consistent with what fastAPI expects for health/get_run responses
        if "created_at" in value and isinstance(value["created_at"], datetime):
            value["created_at"] = value["created_at"].isoformat()
        return value

    def _to_firestore_fields(self, value: dict[str, Any]) -> dict[str, Any]:
        return {key: self._to_firestore_value(item) for key, item in value.items()}

    def _to_firestore_value(self, value: Any) -> dict[str, Any]:
        if value is None:
            return {"nullValue": None}
        if isinstance(value, bool):
            return {"booleanValue": value}
        if isinstance(value, int):
            return {"integerValue": str(value)}
        if isinstance(value, float):
            return {"doubleValue": value}
        if isinstance(value, datetime):
            return {"timestampValue": value.isoformat()}
        if isinstance(value, list):
            return {"arrayValue": {"values": [self._to_firestore_value(item) for item in value]}}
        if isinstance(value, dict):
            return {"mapValue": {"fields": self._to_firestore_fields(value)}}
        return {"stringValue": str(value)}

    def _from_firestore_fields(self, fields: dict[str, Any]) -> dict[str, Any]:
        return {key: self._from_firestore_value(value) for key, value in fields.items()}

    def _from_firestore_value(self, value: dict[str, Any]) -> Any:
        if "nullValue" in value:
            return None
        if "booleanValue" in value:
            return value["booleanValue"]
        if "integerValue" in value:
            return int(value["integerValue"])
        if "doubleValue" in value:
            return value["doubleValue"]
        if "timestampValue" in value:
            return value["timestampValue"]
        if "stringValue" in value:
            return value["stringValue"]
        if "arrayValue" in value:
            return [self._from_firestore_value(item) for item in value["arrayValue"].get("values", [])]
        if "mapValue" in value:
            return self._from_firestore_fields(value["mapValue"].get("fields", {}))
        return None


run_repository = FirebaseRunRepository()
