"""Gemini 2.5 Computer Use agent — visually drives the GCP Pricing
Calculator inside a real Chromium browser controlled by Playwright.

Based on the official google-gemini/computer-use-preview reference
implementation."""

from __future__ import annotations

import base64
import os
import sys
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Literal, Union

from google import genai
from google.genai import types
from google.genai.types import (
    Part,
    Content,
    GenerateContentConfig,
    FunctionResponse,
    FinishReason,
)
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

import playwright.sync_api

COMPUTER_USE_MODEL = "gemini-2.5-computer-use-preview-10-2025"
FLASH_MODEL = "gemini-2.5-flash"

GCP_CALCULATOR_URL = "https://cloud.google.com/products/calculator"

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 900

PLAYWRIGHT_KEY_MAP = {
    "backspace": "Backspace", "tab": "Tab", "return": "Enter", "enter": "Enter",
    "shift": "Shift", "control": "ControlOrMeta", "alt": "Alt", "escape": "Escape",
    "space": "Space", "pageup": "PageUp", "pagedown": "PageDown",
    "end": "End", "home": "Home",
    "left": "ArrowLeft", "up": "ArrowUp", "right": "ArrowRight", "down": "ArrowDown",
    "insert": "Insert", "delete": "Delete",
    "f1": "F1", "f2": "F2", "f3": "F3", "f4": "F4",
    "f5": "F5", "f6": "F6", "f7": "F7", "f8": "F8",
    "f9": "F9", "f10": "F10", "f11": "F11", "f12": "F12",
    "command": "Meta",
}

MAX_RECENT_SCREENSHOTS = 3

PREDEFINED_FUNCTIONS = [
    "open_web_browser", "click_at", "hover_at", "type_text_at",
    "scroll_document", "scroll_at", "wait_5_seconds", "go_back",
    "go_forward", "search", "navigate", "key_combination", "drag_and_drop",
]


def _get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY", "")
    project = os.getenv("VERTEXAI_PROJECT", "")
    if os.getenv("USE_VERTEXAI", "").lower() in ("true", "1") and project:
        return genai.Client(
            vertexai=True, project=project,
            location=os.getenv("VERTEXAI_LOCATION", "us-central1"),
        )
    if api_key:
        return genai.Client(api_key=api_key)
    raise RuntimeError("Set GEMINI_API_KEY or (USE_VERTEXAI + VERTEXAI_PROJECT) in .env")


def _denorm_x(x: int) -> int:
    return int(x / 1000 * SCREEN_WIDTH)

def _denorm_y(y: int) -> int:
    return int(y / 1000 * SCREEN_HEIGHT)


@dataclass
class StepRecord:
    action: str
    details: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class AgentResult:
    success: bool
    monthly_cost: str = ""
    steps: list[StepRecord] = field(default_factory=list)
    error: str = ""
    summary: str = ""
    calculator_url: str = ""


# ---------------------------------------------------------------------------
# Persistent browser session
# ---------------------------------------------------------------------------

class BrowserSession:
    """Keeps a Chromium browser alive across multiple pricing jobs."""

    def __init__(self):
        self._pw = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    @property
    def is_alive(self) -> bool:
        try:
            if self._page is None or self._browser is None:
                print("[session] is_alive: page or browser is None")
                return False
            title = self._page.title()
            print(f"[session] is_alive: True (title={title[:30]})")
            return True
        except Exception as e:
            print(f"[session] is_alive: False ({e})")
            return False

    def ensure_started(self, headless: bool = False) -> Page:
        if self.is_alive:
            return self._page
        self.close()
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(
            headless=headless,
            args=["--disable-extensions", "--disable-dev-shm-usage"],
        )
        self._context = self._browser.new_context(
            viewport={"width": SCREEN_WIDTH, "height": SCREEN_HEIGHT},
        )
        self._page = self._context.new_page()

        def _on_new_page(new_page: playwright.sync_api.Page):
            url = new_page.url
            new_page.close()
            self._page.goto(url)

        self._context.on("page", _on_new_page)
        self._page.goto(GCP_CALCULATOR_URL, wait_until="domcontentloaded", timeout=30_000)
        self._page.wait_for_load_state()
        time.sleep(2)
        return self._page

    def get_url(self) -> str:
        try:
            return self._page.url if self._page else ""
        except Exception:
            return ""

    def screenshot(self) -> bytes | None:
        try:
            return self._page.screenshot(type="png", full_page=False) if self._page else None
        except Exception:
            return None

    def close(self):
        try:
            if self._browser:
                self._browser.close()
        except Exception:
            pass
        try:
            if self._pw:
                self._pw.stop()
        except Exception:
            pass
        self._pw = self._browser = self._context = self._page = None


# Global singleton
browser_session = BrowserSession()


# ---------------------------------------------------------------------------
# Browser computer wrapper
# ---------------------------------------------------------------------------

class _BrowserComputer:
    def __init__(self, page: Page):
        self._page = page

    def _state(self) -> tuple[bytes, str]:
        self._page.wait_for_load_state()
        time.sleep(0.5)
        return self._page.screenshot(type="png", full_page=False), self._page.url

    def open_web_browser(self): return self._state()

    def click_at(self, x, y):
        self._page.mouse.click(x, y); self._page.wait_for_load_state(); return self._state()

    def hover_at(self, x, y):
        self._page.mouse.move(x, y); self._page.wait_for_load_state(); return self._state()

    def type_text_at(self, x, y, text, press_enter=False, clear_before_typing=True):
        self._page.mouse.click(x, y); self._page.wait_for_load_state()
        if clear_before_typing:
            self._page.keyboard.press("ControlOrMeta+a"); self._page.keyboard.press("Delete")
        self._page.keyboard.type(text); self._page.wait_for_load_state()
        if press_enter:
            self._page.keyboard.press("Enter"); self._page.wait_for_load_state()
        return self._state()

    def scroll_document(self, direction):
        if direction == "down": self._page.keyboard.press("PageDown")
        elif direction == "up": self._page.keyboard.press("PageUp")
        elif direction in ("left", "right"):
            sign = "-" if direction == "left" else ""
            self._page.evaluate(f"window.scrollBy({sign}{SCREEN_WIDTH//2}, 0)")
        self._page.wait_for_load_state(); return self._state()

    def scroll_at(self, x, y, direction, magnitude=800):
        self._page.mouse.move(x, y)
        dx, dy = 0, 0
        if direction == "up": dy = -magnitude
        elif direction == "down": dy = magnitude
        elif direction == "left": dx = -magnitude
        elif direction == "right": dx = magnitude
        self._page.mouse.wheel(dx, dy); self._page.wait_for_load_state(); return self._state()

    def wait_5_seconds(self): time.sleep(5); return self._state()
    def go_back(self): self._page.go_back(); self._page.wait_for_load_state(); return self._state()
    def go_forward(self): self._page.go_forward(); self._page.wait_for_load_state(); return self._state()
    def search(self): return self.navigate("https://www.google.com")

    def navigate(self, url):
        if not url.startswith(("http://", "https://")): url = "https://" + url
        self._page.goto(url); self._page.wait_for_load_state(); return self._state()

    def key_combination(self, keys):
        keys = [PLAYWRIGHT_KEY_MAP.get(k.lower(), k) for k in keys]
        for k in keys[:-1]: self._page.keyboard.down(k)
        self._page.keyboard.press(keys[-1])
        for k in reversed(keys[:-1]): self._page.keyboard.up(k)
        return self._state()

    def drag_and_drop(self, x, y, dx, dy):
        self._page.mouse.move(x, y); self._page.mouse.down()
        self._page.mouse.move(dx, dy); self._page.mouse.up()
        return self._state()


def _handle_action(comp, fc):
    name, args = fc.name, dict(fc.args) if fc.args else {}
    if name == "open_web_browser": return comp.open_web_browser()
    if name == "click_at": return comp.click_at(_denorm_x(int(args["x"])), _denorm_y(int(args["y"])))
    if name == "hover_at": return comp.hover_at(_denorm_x(int(args["x"])), _denorm_y(int(args["y"])))
    if name == "type_text_at":
        return comp.type_text_at(_denorm_x(int(args["x"])), _denorm_y(int(args["y"])),
            text=str(args.get("text","")), press_enter=bool(args.get("press_enter",False)),
            clear_before_typing=bool(args.get("clear_before_typing",True)))
    if name == "scroll_document": return comp.scroll_document(str(args["direction"]))
    if name == "scroll_at":
        mag = int(args.get("magnitude",800)); d = str(args["direction"])
        mag = _denorm_y(mag) if d in ("up","down") else _denorm_x(mag)
        return comp.scroll_at(_denorm_x(int(args["x"])), _denorm_y(int(args["y"])), d, mag)
    if name == "wait_5_seconds": return comp.wait_5_seconds()
    if name == "go_back": return comp.go_back()
    if name == "go_forward": return comp.go_forward()
    if name == "search": return comp.search()
    if name == "navigate": return comp.navigate(str(args["url"]))
    if name == "key_combination": return comp.key_combination(str(args["keys"]).split("+"))
    if name == "drag_and_drop":
        return comp.drag_and_drop(_denorm_x(int(args["x"])), _denorm_y(int(args["y"])),
            _denorm_x(int(args["destination_x"])), _denorm_y(int(args["destination_y"])))
    raise ValueError(f"Unknown function: {name}")


def _prune_old_screenshots(contents):
    count = 0
    for content in reversed(contents):
        if content.role != "user" or not content.parts: continue
        has_ss = any(p.function_response and p.function_response.parts
            and p.function_response.name in PREDEFINED_FUNCTIONS for p in content.parts)
        if has_ss:
            count += 1
            if count > MAX_RECENT_SCREENSHOTS:
                for p in content.parts:
                    if (p.function_response and p.function_response.parts
                            and p.function_response.name in PREDEFINED_FUNCTIONS):
                        p.function_response.parts = None


# ---------------------------------------------------------------------------
# Main agent entry point
# ---------------------------------------------------------------------------

def run_pricing_agent(
    resource_spec: dict,
    *,
    headless: bool = False,
    max_steps: int = 40,
    timeout_sec: int = 300,
    on_step: callable = None,
    get_guidance: callable = None,
    add_to_estimate: bool = False,
    resume_url: str = "",
) -> AgentResult:
    """Open the GCP Pricing Calculator and fill in *resource_spec*.

    If *add_to_estimate* is True, reuse the existing browser session so
    the new resource is added to the running total.
    """
    client = _get_client()
    result = AgentResult(success=False)
    start = time.time()

    spec_text = "\n".join(f"  {k}: {v}" for k, v in resource_spec.items() if v)

    if add_to_estimate:
        user_prompt = (
            f"I want to ADD another resource to the existing estimate.\n"
            f"Here is the new GCP resource:\n{spec_text}\n\n"
            "IMPORTANT: The calculator is already open with previous resources. "
            "DO NOT navigate away or reload the page. "
            "Look for the 'Add to estimate' button on the current page and click it "
            "to add a new product. Then configure this new resource. "
            "When done, tell me the updated TOTAL monthly cost (for all resources combined). "
            "Here is a screenshot of the current calculator state:"
        )
    else:
        user_prompt = (
            f"Here is the GCP resource I need priced:\n{spec_text}\n\n"
            "Please go to the Google Cloud Pricing Calculator, configure this "
            "resource, and tell me the estimated monthly cost."
        )

    config = GenerateContentConfig(
        temperature=1, top_p=0.95, top_k=40, max_output_tokens=8192,
        tools=[types.Tool(computer_use=types.ComputerUse(
            environment=types.Environment.ENVIRONMENT_BROWSER))],
    )

    pw_ctx = None
    browser = None
    try:
        pw_ctx = sync_playwright().start()
        browser = pw_ctx.chromium.launch(
            headless=headless,
            args=["--disable-extensions", "--disable-dev-shm-usage"],
        )
        context = browser.new_context(
            viewport={"width": SCREEN_WIDTH, "height": SCREEN_HEIGHT},
        )
        page = context.new_page()

        def _on_new_page(np):
            u = np.url; np.close(); page.goto(u)
        context.on("page", _on_new_page)

        start_url = resume_url if (add_to_estimate and resume_url) else GCP_CALCULATOR_URL
        page.goto(start_url, wait_until="domcontentloaded", timeout=45_000)
        page.wait_for_load_state()
        time.sleep(3)

        result.steps.append(StepRecord(
            action="navigate",
            details=f"Opened {'saved estimate' if resume_url else 'fresh calculator'}",
        ))
        comp = _BrowserComputer(page)

        current_screenshot = page.screenshot(type="png", full_page=False)

        if add_to_estimate and resume_url:
            contents: list[Content] = [Content(role="user", parts=[
                Part(text=user_prompt),
                Part.from_bytes(data=current_screenshot, mime_type="image/png"),
            ])]
        else:
            contents: list[Content] = [Content(role="user", parts=[Part(text=user_prompt)])]

        if on_step:
            on_step(1, "Calculator ready", current_screenshot)

        for step_idx in range(max_steps):
            if time.time() - start > timeout_sec:
                result.error = "Timed out"; break

            try:
                response = client.models.generate_content(
                    model=COMPUTER_USE_MODEL, contents=contents, config=config)
            except Exception as e:
                print(f"[agent] generate_content error: {e}")
                result.error = str(e); break

            if not response.candidates:
                result.error = "No candidates in response"; break

            candidate = response.candidates[0]
            parts = candidate.content.parts if candidate.content else []
            if candidate.content:
                contents.append(candidate.content)

            text_parts, function_calls = [], []
            for part in parts:
                if part.function_call: function_calls.append(part.function_call)
                if part.text: text_parts.append(part.text)

            if (not function_calls and not text_parts
                    and candidate.finish_reason == FinishReason.MALFORMED_FUNCTION_CALL):
                continue

            if not function_calls:
                full_text = " ".join(text_parts).strip()
                if full_text:
                    result.summary = full_text
                    result.monthly_cost = full_text
                    result.success = True
                break

            fr_parts = []
            for fc in function_calls:
                desc = f"{fc.name}({dict(fc.args) if fc.args else {}})"
                result.steps.append(StepRecord(action=fc.name, details=desc))
                print(f"[agent] step {step_idx}: {fc.name}")

                extra = {}
                if fc.args and fc.args.get("safety_decision"):
                    extra["safety_acknowledgement"] = "true"

                try:
                    screenshot_bytes, url = _handle_action(comp, fc)
                except Exception as e:
                    print(f"[agent] action error: {e}")
                    screenshot_bytes, url = comp._state()

                if on_step:
                    on_step(len(result.steps), desc, screenshot_bytes)

                fr_parts.append(Part(function_response=FunctionResponse(
                    name=fc.name, response={"url": url, **extra},
                    parts=[types.FunctionResponsePart(
                        inline_data=types.FunctionResponseBlob(
                            mime_type="image/png", data=screenshot_bytes))])))

            contents.append(Content(role="user", parts=fr_parts))
            _prune_old_screenshots(contents)

            if get_guidance:
                guidance = get_guidance()
                if guidance:
                    print(f"[agent] user guidance: {guidance}")
                    result.steps.append(StepRecord(action="user_guidance", details=guidance))
                    contents.append(Content(role="user",
                        parts=[Part(text=f"USER INSTRUCTION: {guidance}. Please adjust your actions accordingly.")]))

    except Exception as exc:
        result.error = f"{type(exc).__name__}: {exc}"
        traceback.print_exc()
    finally:
        try:
            if page:
                result.calculator_url = page.url
        except Exception:
            pass
        try:
            if browser:
                browser.close()
        except Exception:
            pass
        try:
            if pw_ctx:
                pw_ctx.stop()
        except Exception:
            pass

    return result


def describe_steps(steps: list[StepRecord]) -> str:
    if not steps: return "No steps recorded."
    client = _get_client()
    actions = "\n".join(f"{i+1}. {s.action} — {s.details}" for i, s in enumerate(steps))
    resp = client.models.generate_content(
        model=FLASH_MODEL,
        contents=("Summarise the following browser agent actions into 3-5 bullet points "
                  "that a non-technical user can understand:\n\n" + actions),
        config=GenerateContentConfig(temperature=0.3))
    return resp.text.strip()
