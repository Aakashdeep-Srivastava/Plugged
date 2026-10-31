"""Vercel serverless entry point for the PLUGGED public demo.

Vercel's Python runtime serves the module-level ``app`` (an ASGI FastAPI app).
All routes (/, /static/*, /api/*) are handled by that app; vercel.json rewrites
every path here.

Secrets (QLOO_API_KEY, ANTHROPIC_API_KEY) come from Vercel project environment
variables — never from the repo.
"""

import sys
from pathlib import Path

# Make the repo root importable so `plugged` resolves on the serverless runtime.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from plugged.demo_app import app  # noqa: E402

__all__ = ["app"]
