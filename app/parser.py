"""Gemini 2.5 Flash — parse a plain-English GCP resource request into
a structured dict the computer-use agent can act on."""

from __future__ import annotations

import json
import os
from google import genai
from google.genai import types

FLASH_MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT = """\
You are a GCP pricing expert. The user will describe cloud resources in
plain English. Return a JSON object with exactly these fields (omit any
that don't apply):

{
  "service": "compute_engine | cloud_sql | gke | cloud_storage | ...",
  "machine_type": "e2-standard-2 | n1-standard-4 | ...",
  "vcpus": 2,
  "memory_gb": 4,
  "gpu_type": "nvidia-tesla-t4 | ...",
  "gpu_count": 1,
  "os": "free (debian/ubuntu) | paid (windows/rhel/sles)",
  "region": "us-central1",
  "disk_type": "pd-standard | pd-ssd | pd-balanced",
  "disk_size_gb": 100,
  "hours_per_month": 730,
  "quantity": 1,
  "notes": "any extra context"
}

If you're unsure of a value, pick the most common default.
Return ONLY valid JSON, no markdown fences."""


def _get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY", "")
    project = os.getenv("VERTEXAI_PROJECT", "")

    if os.getenv("USE_VERTEXAI", "").lower() == "true" and project:
        return genai.Client(
            vertexai=True,
            project=project,
            location=os.getenv("VERTEXAI_LOCATION", "us-central1"),
        )
    if api_key:
        return genai.Client(api_key=api_key)
    raise RuntimeError(
        "Set GEMINI_API_KEY or (USE_VERTEXAI + VERTEXAI_PROJECT) in .env"
    )


def parse_resource_request(user_text: str) -> dict:
    """Send *user_text* to Gemini Flash and return a parsed resource dict."""
    client = _get_client()
    response = client.models.generate_content(
        model=FLASH_MODEL,
        contents=user_text,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.0,
        ),
    )
    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(raw)
