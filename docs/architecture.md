# AgentMesh Architecture

AgentMesh is organized as a deterministic agent pipeline. Each agent returns structured findings so a developer can audit the debugging and CI/CD decision trail.

## Flow

1. A client posts a run request to `POST /api/runs`.
2. The backend converts the request into a `PipelineTask`.
3. `ManagerAgent` computes a CI/CD risk score.
4. Specialized agents run in order: debug, fix, test, deploy, monitor.
5. The backend returns status, risk, and agent findings.

## Extension Ideas

- Add repository checkout and sandboxed command execution.
- Store runs in a database.
- Connect to GitHub Actions or GitLab CI webhooks.
- Replace the heuristic risk score with the trained model from `ml/train.py`.
- Add authenticated deployment approvals for production.
