"""FastAPI entry-point for the GCP Pricing Calculator Agent."""

from __future__ import annotations

import os
import uuid
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

from app.parser import parse_resource_request  # noqa: E402
from app.agent import run_pricing_agent, describe_steps, AgentResult  # noqa: E402

app = FastAPI(title="GCP Pricing Calculator Agent")

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

executor = ThreadPoolExecutor(max_workers=2)

jobs: dict[str, dict] = {}


class PriceRequest(BaseModel):
    query: str
    headless: bool = True


class JobStatus(BaseModel):
    job_id: str
    status: str
    monthly_cost: str | None = None
    summary: str | None = None
    step_count: int = 0
    error: str | None = None
    duration_sec: float | None = None


@app.get("/", response_class=HTMLResponse)
async def index():
    return (STATIC_DIR / "index.html").read_text()


@app.get("/api/health")
async def health():
    has_key = bool(os.getenv("GEMINI_API_KEY") or os.getenv("VERTEXAI_PROJECT"))
    return {"status": "ok", "gemini_configured": has_key}


def _run_job(job_id: str, query: str, headless: bool) -> None:
    """Background worker that parses, runs the agent, and writes results."""
    job = jobs[job_id]
    try:
        job["status"] = "parsing"
        resource_spec = parse_resource_request(query)
        job["parsed_spec"] = resource_spec

        job["status"] = "running_agent"
        result: AgentResult = run_pricing_agent(
            resource_spec, headless=headless, max_steps=40, timeout_sec=180
        )

        job["status"] = "done" if result.success else "failed"
        job["monthly_cost"] = result.monthly_cost
        job["error"] = result.error or None
        job["step_count"] = len(result.steps)
        job["end_time"] = time.time()

        if result.steps:
            try:
                job["summary"] = describe_steps(result.steps)
            except Exception:
                job["summary"] = f"{len(result.steps)} browser actions executed."
    except Exception as exc:
        job["status"] = "failed"
        job["error"] = str(exc)
        job["end_time"] = time.time()


@app.post("/api/price", response_model=JobStatus)
async def start_pricing(req: PriceRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="query is required")

    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {
        "status": "queued",
        "query": req.query,
        "start_time": time.time(),
        "end_time": None,
        "monthly_cost": None,
        "summary": None,
        "step_count": 0,
        "error": None,
        "parsed_spec": None,
    }
    executor.submit(_run_job, job_id, req.query, req.headless)
    return JobStatus(job_id=job_id, status="queued")


@app.get("/api/price/{job_id}", response_model=JobStatus)
async def get_pricing_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    duration = None
    if job.get("start_time"):
        end = job.get("end_time") or time.time()
        duration = round(end - job["start_time"], 1)
    return JobStatus(
        job_id=job_id,
        status=job["status"],
        monthly_cost=job.get("monthly_cost"),
        summary=job.get("summary"),
        step_count=job.get("step_count", 0),
        error=job.get("error"),
        duration_sec=duration,
    )


@app.get("/api/jobs")
async def list_jobs():
    return [
        {"job_id": jid, "status": j["status"], "query": j.get("query", "")}
        for jid, j in jobs.items()
    ]
