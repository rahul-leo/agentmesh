"""Built-in heuristic risk predictor for AgentMesh."""

from __future__ import annotations


def predict_failure_risk(
    failure_log: str = "",
    changed_files: list[str] | None = None,
    environment: str = "local",
) -> dict:
    """Estimate pipeline risk without optional ML dependencies."""

    log = failure_log.lower()
    files = changed_files or []
    score = 0.1
    reasons: list[str] = []

    if log:
        score += 0.2
        reasons.append("failure log supplied")

    for keyword in ("syntaxerror", "assertionerror", "timeout", "connection refused", "migration", "rollback"):
        if keyword in log:
            score += 0.12
            reasons.append(f"detected {keyword}")

    if any(path.startswith(("backend/", "agents/", "docker/")) for path in files):
        score += 0.15
        reasons.append("backend or infrastructure files changed")

    if any(path.endswith(("requirements.txt", "package.json", "package-lock.json")) for path in files):
        score += 0.1
        reasons.append("dependency files changed")

    if environment == "production":
        score += 0.25
        reasons.append("production environment")
    elif environment == "staging":
        score += 0.1
        reasons.append("staging environment")

    score = min(round(score, 2), 1.0)
    if score >= 0.7:
        label = "high"
    elif score >= 0.4:
        label = "medium"
    else:
        label = "low"

    return {
        "risk_score": score,
        "risk_label": label,
        "reasons": reasons,
    }
