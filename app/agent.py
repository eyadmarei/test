"""Gemini 2.5 Computer Use agent — visually drives the GCP Pricing
Calculator inside a real Chromium browser controlled by Playwright."""

from __future__ import annotations

import base64
import io
import os
import time
import traceback
from dataclasses import dataclass, field
from typing import Any

from google import genai
from google.genai import types
from playwright.sync_api import sync_playwright, Page, Browser

COMPUTER_USE_MODEL = "gemini-2.5-computer-use-preview-10-2025"
FLASH_MODEL = "gemini-2.5-flash"

GCP_CALCULATOR_URL = "https://cloud.google.com/products/calculator"

VIEWPORT = {"width": 1280, "height": 900}

SYSTEM_INSTRUCTION = """\
You are an expert at using the Google Cloud Pricing Calculator website.
You will receive a structured resource specification. Your job is to:
1. Navigate to the pricing calculator if not already there.
2. Add the requested resources by interacting with the UI.
3. Configure all fields to match the spec (machine type, vCPUs, RAM, region, OS, disk, etc.).
4. Once configured, read the estimated monthly cost from the page.
5. Return the final monthly cost as your last message.

Be patient — the page may take time to load. Wait for elements before clicking.
If a field is already set to the correct value, skip it.
Prefer clicking visible UI elements over typing when possible.
"""


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


def _screenshot_b64(page: Page) -> str:
    png_bytes = page.screenshot(type="png")
    return base64.b64encode(png_bytes).decode()


def _make_image_part(b64: str) -> types.Part:
    return types.Part.from_bytes(data=base64.b64decode(b64), mime_type="image/png")


@dataclass
class StepRecord:
    action: str
    details: str = ""
    screenshot_b64: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class AgentResult:
    success: bool
    monthly_cost: str = ""
    steps: list[StepRecord] = field(default_factory=list)
    error: str = ""
    summary: str = ""


def _execute_action(page: Page, action: dict) -> str:
    """Execute a single computer-use action returned by the model.

    Returns a short human description of what was done.
    """
    action_type = action.get("type", action.get("action", ""))

    if action_type in ("click", "mouse_click"):
        x = int(action.get("x", 0))
        y = int(action.get("y", 0))
        button = action.get("button", "left")
        page.mouse.click(x, y, button=button)
        return f"click ({x}, {y})"

    if action_type in ("type", "key_type", "input_text"):
        text = action.get("text", action.get("value", ""))
        page.keyboard.type(text, delay=30)
        return f"type '{text[:40]}'"

    if action_type in ("key", "key_press", "press"):
        key = action.get("key", action.get("value", ""))
        page.keyboard.press(key)
        return f"press '{key}'"

    if action_type == "scroll":
        x = int(action.get("x", VIEWPORT["width"] // 2))
        y = int(action.get("y", VIEWPORT["height"] // 2))
        dx = int(action.get("delta_x", action.get("scroll_x", 0)))
        dy = int(action.get("delta_y", action.get("scroll_y", 0)))
        page.mouse.move(x, y)
        page.mouse.wheel(dx, dy)
        return f"scroll ({dx}, {dy}) at ({x}, {y})"

    if action_type in ("navigate", "goto"):
        url = action.get("url", "")
        page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        return f"navigate to {url[:60]}"

    if action_type == "wait":
        ms = int(action.get("duration", action.get("ms", 1000)))
        time.sleep(ms / 1000)
        return f"wait {ms}ms"

    if action_type in ("screenshot", "observe"):
        return "observe (screenshot)"

    if action_type in ("drag", "mouse_drag"):
        sx, sy = int(action.get("start_x", 0)), int(action.get("start_y", 0))
        ex, ey = int(action.get("end_x", 0)), int(action.get("end_y", 0))
        page.mouse.move(sx, sy)
        page.mouse.down()
        page.mouse.move(ex, ey)
        page.mouse.up()
        return f"drag ({sx},{sy})→({ex},{ey})"

    return f"unknown action: {action_type}"


def _build_tool() -> types.Tool:
    return types.Tool(
        computer_use=types.ToolComputerUse(
            environment=types.Environment(
                display_width=VIEWPORT["width"],
                display_height=VIEWPORT["height"],
            )
        )
    )


def run_pricing_agent(
    resource_spec: dict,
    *,
    headless: bool = True,
    max_steps: int = 40,
    timeout_sec: int = 180,
) -> AgentResult:
    """Open the GCP Pricing Calculator and fill in *resource_spec*.

    Returns an AgentResult with the estimated monthly cost.
    """
    client = _get_client()
    result = AgentResult(success=False)
    start = time.time()

    spec_text = "\n".join(f"  {k}: {v}" for k, v in resource_spec.items() if v)
    user_prompt = (
        f"Here is the GCP resource I need priced:\n{spec_text}\n\n"
        "Please go to the Google Cloud Pricing Calculator, configure this "
        "resource, and tell me the estimated monthly cost."
    )

    with sync_playwright() as pw:
        browser: Browser = pw.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            viewport=VIEWPORT,
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        try:
            page.goto(GCP_CALCULATOR_URL, wait_until="domcontentloaded", timeout=30_000)
            page.wait_for_timeout(3000)

            result.steps.append(StepRecord(
                action="navigate",
                details=f"Opened {GCP_CALCULATOR_URL}",
                screenshot_b64=_screenshot_b64(page),
            ))

            screenshot = _screenshot_b64(page)
            messages: list[types.Content] = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=user_prompt),
                        _make_image_part(screenshot),
                    ],
                )
            ]

            for step_idx in range(max_steps):
                if time.time() - start > timeout_sec:
                    result.error = "Timed out"
                    break

                response = client.models.generate_content(
                    model=COMPUTER_USE_MODEL,
                    contents=messages,
                    config=types.GenerateContentConfig(
                        tools=[_build_tool()],
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.0,
                    ),
                )

                if not response.candidates:
                    result.error = "No candidates in response"
                    break

                candidate = response.candidates[0]
                parts = candidate.content.parts if candidate.content else []

                messages.append(types.Content(role="model", parts=parts))

                has_function_call = False
                text_parts = []

                for part in parts:
                    if part.function_call:
                        has_function_call = True
                        fc = part.function_call
                        action_dict = dict(fc.args) if fc.args else {}
                        action_dict.setdefault("type", fc.name)

                        desc = _execute_action(page, action_dict)
                        page.wait_for_timeout(800)

                        new_screenshot = _screenshot_b64(page)
                        result.steps.append(StepRecord(
                            action=desc,
                            details=str(action_dict),
                            screenshot_b64=new_screenshot,
                        ))

                        messages.append(
                            types.Content(
                                role="user",
                                parts=[
                                    types.Part.from_function_response(
                                        name=fc.name,
                                        response={"status": "ok"},
                                    ),
                                    _make_image_part(new_screenshot),
                                ],
                            )
                        )

                    if part.text:
                        text_parts.append(part.text)

                full_text = "\n".join(text_parts).strip()

                if not has_function_call and full_text:
                    result.summary = full_text
                    for token in ("$", "USD", "month", "cost", "estimate"):
                        if token.lower() in full_text.lower():
                            result.success = True
                            result.monthly_cost = full_text
                            break
                    break

                if not has_function_call and not full_text:
                    result.error = "Model returned empty response"
                    break

        except Exception as exc:
            result.error = f"{type(exc).__name__}: {exc}"
            traceback.print_exc()
        finally:
            browser.close()

    return result


def describe_steps(steps: list[StepRecord]) -> str:
    """Use Gemini Flash to produce a human-readable summary of the agent's
    recorded steps."""
    if not steps:
        return "No steps recorded."
    client = _get_client()
    actions = "\n".join(
        f"{i+1}. {s.action} — {s.details}" for i, s in enumerate(steps)
    )
    resp = client.models.generate_content(
        model=FLASH_MODEL,
        contents=(
            "Summarise the following browser agent actions into 3-5 bullet points "
            "that a non-technical user can understand:\n\n" + actions
        ),
        config=types.GenerateContentConfig(temperature=0.3),
    )
    return resp.text.strip()
