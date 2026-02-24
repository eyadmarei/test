# AGENTS.md

## Cursor Cloud specific instructions

### Overview
GCP Pricing Calculator Agent — a Python/FastAPI web app. The user types a GCP resource request in plain English; a Gemini AI agent visually operates the GCP Pricing Calculator in a real browser (Playwright + Chromium) and returns a monthly cost estimate.

### Stack
- Python 3.9+ (3.12 on this VM)
- **FastAPI + uvicorn** — HTTP server
- **Playwright** (sync, Chromium) — browser automation
- **google-genai** — Gemini API client (supports both AI Studio key and Vertex AI)
  - `gemini-2.5-computer-use-preview-10-2025` — the agent that sees screenshots and clicks
  - `gemini-2.5-flash` — fast model for parsing user input and describing steps
- **python-dotenv** — `.env` config

### Running the app
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Web UI at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

### Key API endpoints
- `GET  /api/health` — health check (also reports whether Gemini is configured)
- `POST /api/price` — submit a pricing query (`{"query": "..."}`)
- `GET  /api/price/{job_id}` — poll job status
- `GET  /api/jobs` — list all jobs

### Key caveats
- **GEMINI_API_KEY required:** Set in `.env` (copy `.env.example`). Without a valid key, the server starts but pricing jobs will fail with `API_KEY_INVALID`. Alternatively, set `USE_VERTEXAI=true` + `VERTEXAI_PROJECT` + `VERTEXAI_LOCATION` for Vertex AI auth.
- **Playwright Chromium:** After `pip install`, also run `python3 -m playwright install --with-deps chromium`.
- **PATH:** pip installs to `~/.local/bin` — ensure it's on `$PATH` for `uvicorn` and `playwright` CLI.
- **No linter or test suite configured:** There is no pytest, flake8, or mypy configured in this project. Python type hints are used but not enforced via tooling.
- **Headless browser:** The computer-use agent launches Chromium headless by default. In the Cloud VM, `xvfb` is pre-installed for headed mode if needed.
