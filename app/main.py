"""FastAPI entry-point for the GCP Pricing Calculator Agent."""

from __future__ import annotations

import os
import uuid
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

from app.parser import parse_resource_request  # noqa: E402
from app.agent import run_pricing_agent, describe_steps, AgentResult, browser_session  # noqa: E402

app = FastAPI(title="GCP Pricing Calculator Agent")

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

executor = ThreadPoolExecutor(max_workers=2)

jobs: dict[str, dict] = {}


class PriceRequest(BaseModel):
    query: str
    headless: bool = False
    add_to_estimate: bool = False


class GuidanceRequest(BaseModel):
    message: str


class JobStatus(BaseModel):
    job_id: str
    status: str
    monthly_cost: str | None = None
    summary: str | None = None
    step_count: int = 0
    error: str | None = None
    duration_sec: float | None = None
    parsed_spec: dict | None = None
    last_action: str | None = None
    has_screenshot: bool = False
    calculator_url: str | None = None


@app.get("/", response_class=HTMLResponse)
async def index():
    return (STATIC_DIR / "index.html").read_text()


@app.get("/api/health")
async def health():
    has_key = bool(os.getenv("GEMINI_API_KEY") or os.getenv("VERTEXAI_PROJECT"))
    return {
        "status": "ok",
        "gemini_configured": has_key,
        "browser_alive": browser_session.is_alive,
    }


def _run_job(job_id: str, query: str, headless: bool, add_to_estimate: bool) -> None:
    job = jobs[job_id]
    try:
        job["status"] = "parsing"
        resource_spec = parse_resource_request(query)
        job["parsed_spec"] = resource_spec
        job["status"] = "running_agent"

        def _on_step(count, action_desc="", screenshot_bytes=None):
            job["step_count"] = count
            if action_desc:
                job["last_action"] = action_desc
            if screenshot_bytes:
                job["latest_screenshot"] = screenshot_bytes

        def _get_guidance():
            msg = job.get("pending_guidance")
            if msg:
                job["pending_guidance"] = None
                return msg
            return None

        result: AgentResult = run_pricing_agent(
            resource_spec,
            headless=headless,
            max_steps=40,
            timeout_sec=300,
            on_step=_on_step,
            get_guidance=_get_guidance,
            add_to_estimate=add_to_estimate,
        )

        job["status"] = "done" if result.success else "failed"
        job["monthly_cost"] = result.monthly_cost
        job["error"] = result.error or None
        job["step_count"] = len(result.steps)
        job["calculator_url"] = result.calculator_url
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
        "last_action": None,
        "latest_screenshot": None,
        "pending_guidance": None,
        "calculator_url": None,
    }
    executor.submit(_run_job, job_id, req.query, req.headless, req.add_to_estimate)
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
        job_id=job_id, status=job["status"],
        monthly_cost=job.get("monthly_cost"), summary=job.get("summary"),
        step_count=job.get("step_count", 0), error=job.get("error"),
        duration_sec=duration, parsed_spec=job.get("parsed_spec"),
        last_action=job.get("last_action"),
        has_screenshot=job.get("latest_screenshot") is not None,
        calculator_url=job.get("calculator_url"),
    )


@app.get("/api/price/{job_id}/screenshot")
async def get_screenshot(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    ss = job.get("latest_screenshot")
    if not ss:
        raise HTTPException(status_code=404, detail="No screenshot yet")
    return Response(content=ss, media_type="image/png")


@app.post("/api/price/{job_id}/guide")
async def send_guidance(job_id: str, req: GuidanceRequest):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "running_agent":
        raise HTTPException(status_code=400, detail="Job is not running")
    job["pending_guidance"] = req.message
    return {"status": "ok", "message": f"Guidance queued: {req.message}"}


@app.post("/api/session/reset")
async def reset_session():
    browser_session.close()
    return {"status": "ok", "message": "Browser session closed. Next job starts fresh."}


@app.get("/api/session/screenshot")
async def session_screenshot():
    ss = browser_session.screenshot()
    if not ss:
        raise HTTPException(status_code=404, detail="No active browser session")
    return Response(content=ss, media_type="image/png")


@app.get("/api/jobs")
async def list_jobs():
    return [
        {"job_id": jid, "status": j["status"], "query": j.get("query", "")}
        for jid, j in jobs.items()
    ]
