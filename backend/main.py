"""FastAPI entrypoint for AgentMesh."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from backend.routes.health import router as health_router
from backend.routes.runs import router as runs_router

app = FastAPI(
    title="AgentMesh API",
    description="Autonomous coding assistant backend for debugging and CI/CD.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://agent-mesh-portal.vercel.app"
    ],
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1):\d+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(runs_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "AgentMesh API is running", "docs": "/docs"}
