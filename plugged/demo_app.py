"""PLUGGED public demo backend (FastAPI).

A deliberately small, PUBLIC-SAFE surface — the opposite of the local dashboard,
which is a single-operator control deck. This app:

  * serves the one-page demo and its icons,
  * exposes ONE action, POST /api/collab, which streams the cultural-partnership
    agent's live activity then its result as NDJSON,
  * calls the model via the Anthropic API (server-side key) and Qloo (server-side
    key) — never a shell, never the local Claude subscription, never email.

It is designed for a serverless host (Vercel): stateless, bounded per run, with a
best-effort in-memory rate cap. Secrets come from the environment only.
"""

import asyncio
import json
import logging
import os
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response, StreamingResponse

logger = logging.getLogger("plugged.demo")

WEB_DEMO_DIR = Path(__file__).resolve().parent / "web_demo"
ICONS_DIR = Path(__file__).resolve().parent / "web" / "icons"

MAX_BRIEF_CHARS = 2000
# Best-effort limits. Serverless resets these on cold start, so treat them as a
# courtesy throttle, not hard security — a real deployment should front this
# with a platform rate limiter / KV counter.
PER_IP_COOLDOWN = float(os.getenv("DEMO_PER_IP_COOLDOWN", "6"))
DAILY_CAP = int(os.getenv("DEMO_DAILY_CAP", "300"))

_BINARY = {".png": "image/png", ".ico": "image/x-icon", ".webmanifest": "application/manifest+json"}

app = FastAPI(title="PLUGGED demo", docs_url=None, redoc_url=None, openapi_url=None)

_last_seen: dict[str, float] = {}
_day = {"date": "", "count": 0}


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "?"


def _rate_limited(ip: str) -> str:
    """Returns a reason string if the request should be refused, else ""."""
    now = time.time()
    today = time.strftime("%Y-%m-%d", time.gmtime(now))
    if _day["date"] != today:
        _day["date"] = today
        _day["count"] = 0
    if _day["count"] >= DAILY_CAP:
        return "The demo has hit today's usage cap. Please try again tomorrow."
    last = _last_seen.get(ip, 0.0)
    if now - last < PER_IP_COOLDOWN:
        return f"One run at a time, please — wait a few seconds and retry."
    _last_seen[ip] = now
    _day["count"] += 1
    return ""


@app.get("/", response_class=HTMLResponse)
async def index():
    try:
        return (WEB_DEMO_DIR / "index.html").read_text(encoding="utf-8")
    except OSError:
        return HTMLResponse("<h1>PLUGGED</h1><p>Demo page missing.</p>", status_code=500)


@app.get("/static/{name}")
async def static_asset(name: str):
    target = (ICONS_DIR / name).resolve()
    if not target.is_file() or not target.is_relative_to(ICONS_DIR.resolve()):
        return Response("not found", status_code=404)
    ext = target.suffix.lower()
    if ext in _BINARY:
        return Response(target.read_bytes(), media_type=_BINARY[ext],
                        headers={"Cache-Control": "public, max-age=604800"})
    return Response(target.read_text(encoding="utf-8"), media_type="text/plain")


@app.get("/api/health")
async def health():
    return {
        "ok": True,
        "qloo_configured": bool(os.getenv("QLOO_API_KEY", "").strip()),
        "model_configured": bool(os.getenv("ANTHROPIC_API_KEY", "").strip()),
    }


@app.post("/api/collab")
async def collab(request: Request):
    """Run the cultural-partnership agent, streaming NDJSON:
      {"type":"event", ...}   one per agent step (live activity)
      {"type":"result","result":{...}}   the final structured result
      {"type":"error","error":"..."}     a user-facing failure
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Send JSON: {\"brief\": \"...\"}"}, status_code=400)
    brief = (body or {}).get("brief") if isinstance(body, dict) else None
    if not isinstance(brief, str) or not brief.strip():
        return JSONResponse({"error": "A brand brief is required."}, status_code=400)
    if len(brief) > MAX_BRIEF_CHARS:
        return JSONResponse({"error": f"Brief is too long (max {MAX_BRIEF_CHARS})."},
                            status_code=400)

    reason = _rate_limited(_client_ip(request))
    if reason:
        return JSONResponse({"error": reason}, status_code=429)

    if not os.getenv("ANTHROPIC_API_KEY", "").strip():
        return JSONResponse({"error": "The demo isn't configured (no model key)."},
                            status_code=503)
    if not os.getenv("QLOO_API_KEY", "").strip():
        return JSONResponse({"error": "The demo isn't configured (no Qloo key)."},
                            status_code=503)

    from plugged.api_brain import AnthropicAPIBrain
    from plugged.collab_agent import CollabAgent
    from plugged.integrations.qloo import QlooClient

    agent = CollabAgent(AnthropicAPIBrain(), QlooClient())
    queue: asyncio.Queue = asyncio.Queue()

    async def on_event(event):
        await queue.put({"type": "event", **event})

    async def driver():
        try:
            result = await agent.run(brief.strip(), on_event=on_event)
            await queue.put({"type": "result", "result": result})
        except Exception as e:
            logger.error("collab run failed (%s)", type(e).__name__)
            await queue.put({"type": "error",
                             "error": "The agent hit an error partway through."})
        finally:
            await queue.put(None)

    async def stream():
        task = asyncio.create_task(driver())
        try:
            while True:
                item = await queue.get()
                if item is None:
                    break
                yield json.dumps(item, ensure_ascii=False) + "\n"
        finally:
            if not task.done():
                task.cancel()

    return StreamingResponse(stream(), media_type="application/x-ndjson",
                             headers={"Cache-Control": "no-store",
                                      "X-Accel-Buffering": "no"})
