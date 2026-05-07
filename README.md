# AgentMesh

AgentMesh is a reusable autonomous debugging and CI/CD assistant. It accepts a repository link, branch, changed files, and a failure log, then coordinates agents that debug the issue, propose fixes, choose tests, prepare deployment, and report a final verdict.

## Requirements

- Python 3.11+
- Node.js 20+
- Git
- Vercel CLI: `npm install -g vercel`
- Optional GitHub CLI for full automation: `winget install GitHub.cli`

## Run Locally

Start the backend:

```powershell
git clone https://github.com/<your-user>/<your-repo>.git
cd <your-repo>
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Start the frontend in another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. The API docs are available at `http://127.0.0.1:8000/docs`.

Optional Streamlit dashboard:

```powershell
pip install -r requirements-streamlit.txt
streamlit run streamlit_app.py
```

## Public Configuration

Copy `.env.example` to `.env` if you want to customize settings:

```powershell
Copy-Item .env.example .env
```

By default, AgentMesh uses in-memory storage so every public clone runs without private Firebase credentials. To use your own Firebase project, set `FIREBASE_USE_MEMORY=false` and fill in your own Firebase values in `.env`.

## Local CI

```powershell
pip install -r requirements-dev.txt
.\scripts\ci.ps1
```

## Deployment Options

AgentMesh supports Vercel and Render launch paths from the dashboard deploy panel and from the deploy-agent result. Render uses a repo-specific `https://render.com/deploy?repo=...` link with `render.yaml` to create the FastAPI web service and static frontend site.

## Optional ML Training

The backend uses a built-in heuristic risk predictor, so `scikit-learn` is not required to run the app. Install optional ML dependencies only when you want to run model training:

```powershell
pip install -r requirements-ml.txt
python ml/train.py
```

## API Endpoints

- `GET /health`
- `GET /health/storage`
- `POST /api/runs`
- `GET /api/runs`
- `GET /api/runs/{run_id}`

## Agents

- `DebugAgent`: classifies logs and detects Vercel, npm, Python, and Selenium failures.
- `FixAgent`: proposes conservative repair steps.
- `AutoFixAgent`: prepares an automated pull request workflow.
- `TestAgent`: selects validation commands.
- `DeployAgent`: checks Vercel readiness and provides deploy links/commands.
- `MonitorAgent`: lists post-deploy signals.
- `VerdictAgent`: summarizes the final release recommendation.
