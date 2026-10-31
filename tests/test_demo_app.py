"""Wiring tests for the public demo backend. Hermetic — no real Qloo/Anthropic
calls (the agent itself is covered by test_collab_agent)."""

import pytest
from fastapi.testclient import TestClient

from plugged.demo_app import app

client = TestClient(app)


def test_index_serves_branded_page():
    r = client.get("/")
    assert r.status_code == 200
    assert "PLUGGED" in r.text
    assert "Unexpected collabs" in r.text


def test_health_reports_config(monkeypatch):
    monkeypatch.delenv("QLOO_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    body = client.get("/api/health").json()
    assert body["ok"] is True
    assert body["qloo_configured"] is False
    assert body["model_configured"] is False


def test_collab_requires_a_brief():
    assert client.post("/api/collab", json={}).status_code == 400
    assert client.post("/api/collab", json={"brief": "   "}).status_code == 400


def test_collab_rejects_overlong_brief():
    assert client.post("/api/collab", json={"brief": "x" * 5000}).status_code == 400


def test_collab_503_without_keys(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("QLOO_API_KEY", raising=False)
    r = client.post("/api/collab", json={"brief": "A real brief here."})
    assert r.status_code == 503
