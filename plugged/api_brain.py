"""AnthropicAPIBrain — a model "brain" backed by the Anthropic API.

PLUGGED's local dashboard can think with the operator's Claude Code subscription
(the inherited CLI Brain in plugged/brain.py). The PUBLIC, hosted demo cannot:
that CLI is bound to one person's subscription login and has no API-key path.
This brain fills that gap — it calls the Anthropic API with a server-side key and
exposes the same ``think`` / ``think_json`` surface the agents already use, so the
agent code is identical in both places.

It uses NO tools (like the CLI Brain's ``--tools ""`` isolation): the prompts
carry untrusted brand briefs and scraped/Qloo text, so the model is given data to
read, never tools to act with.
"""

import json
import logging
import os
import re

logger = logging.getLogger("plugged.api_brain")

# Authoritative current model ids. Sonnet 5 balances quality, cost and latency
# for a public demo doing multi-step reasoning; override with ANTHROPIC_MODEL.
DEFAULT_MODEL = "claude-sonnet-5"
DEFAULT_MAX_TOKENS = 4096


class AnthropicAPIBrain:
    def __init__(self, api_key: str = "", model: str = "",
                 max_tokens: int = DEFAULT_MAX_TOKENS, system: str = ""):
        self.api_key = (api_key or os.getenv("ANTHROPIC_API_KEY", "")).strip()
        self.model = (model or os.getenv("ANTHROPIC_MODEL", "") or DEFAULT_MODEL).strip()
        self.max_tokens = max_tokens
        self.system = system
        self.provider = "anthropic_api"
        self.last_reply_empty = False
        self._client = None

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def _ensure_client(self):
        if self._client is None:
            if not self.api_key:
                raise RuntimeError(
                    "ANTHROPIC_API_KEY is not set — the hosted brain needs it.")
            from anthropic import AsyncAnthropic
            self._client = AsyncAnthropic(api_key=self.api_key)
        return self._client

    async def think(self, prompt: str, session_id: str | None = None,
                    agent: str = "", task: str = "", **_) -> str:
        """One tool-less completion. Returns "" on failure (callers handle empty)."""
        try:
            client = self._ensure_client()
            kwargs = {"model": self.model, "max_tokens": self.max_tokens,
                      "messages": [{"role": "user", "content": prompt}]}
            if self.system:
                kwargs["system"] = self.system
            resp = await client.messages.create(**kwargs)
        except Exception as e:
            # Log the type only; messages can carry prompt content.
            logger.error(f"Anthropic API call failed ({type(e).__name__}).")
            return ""
        parts = [b.text for b in getattr(resp, "content", [])
                 if getattr(b, "type", "") == "text"]
        return "".join(parts).strip()

    async def think_json(self, prompt: str, session_id: str | None = None,
                         agent: str = "", task: str = "", **_):
        """Send a prompt and parse the reply as JSON (same contract as Brain).

        Self-contained on purpose: the hosted demo imports only this module, so
        it must not pull in the local CLI Brain (and its state/sqlite deps).
        """
        full = prompt + "\n\nRespond ONLY with valid JSON. No markdown, no explanation."
        text = await self.think(full, agent=agent, task=task)
        self.last_reply_empty = not text
        if not text:
            return None
        parsed = _extract_json(text)
        if parsed is None:
            logger.error(f"Could not parse JSON from model reply: {text[:200]}")
        return parsed


def _extract_json(text: str):
    """Best-effort JSON extraction: strip code fences, else find the outermost
    object/array in surrounding prose. (Same behaviour as Brain._extract_json.)"""
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    for open_ch, close_ch in (("{", "}"), ("[", "]")):
        start = cleaned.find(open_ch)
        end = cleaned.rfind(close_ch)
        if start != -1 and end > start:
            try:
                return json.loads(cleaned[start:end + 1])
            except json.JSONDecodeError:
                continue
    return None
