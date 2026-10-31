"""End-to-end test for the CollabAgent orchestration.

Uses a fake brain (canned JSON per step) and a Qloo MockTransport (labeled mock
fixtures). No real API calls. Proves the agent resolves a seed, explores a
category, preserves Qloo's affinity/tags verbatim, keeps business feasibility as
a separate (model) field, and holds outreach drafts for approval.
"""

import httpx
import pytest

from plugged.collab_agent import CollabAgent
from plugged.integrations.qloo import QlooClient


class FakeBrain:
    """Returns canned JSON keyed by the agent step (task)."""
    provider = "fake"

    async def think_json(self, prompt, session_id=None, agent="", task="", **_):
        if task == "understand":
            return {
                "brand_name": "Aperture Coffee",
                "category": "coffee",
                "audience": "urban creatives who care about provenance",
                "cultural_descriptors": ["third-wave", "minimal", "design-led"],
                "target_categories": ["music"],
            }
        if task == "decide_query":
            return {"query_more": False, "category": "", "why": "enough signal"}
        if task == "analyze":
            return {"candidates": [
                {"id": "MOCK-ARTIST-1",
                 "cultural_rationale": "Shared indie/design-led taste.",
                 "business_feasibility": {"assessment": "Plausible pop-up tie-in.",
                                          "confidence": "medium",
                                          "unknowns": ["budget", "schedules"]},
                 "concept": "A limited espresso blend launched at the band's shows.",
                 "outreach_draft": "Hi — we think our audiences overlap..."},
            ]}
        return None


def qloo_mock():
    def handler(request):
        path = request.url.path
        if path == "/search":
            return httpx.Response(200, json={"results": [
                {"entity_id": "MOCK-BRAND-1", "name": "Aperture Coffee",
                 "types": ["urn:entity:brand"]}]})
        if path == "/v2/insights":
            return httpx.Response(200, json={"results": {"entities": [
                {"entity_id": "MOCK-ARTIST-1", "name": "The Fictional Band",
                 "types": ["urn:entity:artist"], "query": {"affinity": 0.88},
                 "tags": [{"name": "indie"}], "properties": {}},
            ]}})
        return httpx.Response(200, json={"results": []})
    return QlooClient(api_key="MOCK-KEY", transport=httpx.MockTransport(handler))


@pytest.mark.asyncio
async def test_agent_returns_evidence_backed_candidates():
    events = []
    agent = CollabAgent(FakeBrain(), qloo_mock())
    result = await agent.run("We are Aperture Coffee, looking for a music collab.",
                             on_event=lambda e: events.append(e) or _noop())

    cands = result["candidates"]
    assert len(cands) == 1
    c = cands[0]
    # Qloo evidence preserved verbatim.
    assert c["qloo_affinity"] == 0.88
    assert "indie" in c["qloo_tags"]
    # Business feasibility is a SEPARATE, model-sourced field.
    assert c["business_feasibility"]["confidence"] == "medium"
    assert c["cultural_rationale"]
    # Top candidate carries a concept + an approval-gated draft.
    assert c["concept"]
    assert c["outreach_draft"]
    assert c["approval_required"] is True
    # Transparency + honesty.
    assert any(q["endpoint"] == "/v2/insights" for q in result["qloo_queries"])
    assert "does not predict partnership success" in result["disclaimer"]
    assert result["activity"]


async def _noop():
    return None


@pytest.mark.asyncio
async def test_agent_handles_no_seed_gracefully():
    def handler(request):
        return httpx.Response(200, json={"results": []})  # Qloo finds nothing
    qloo = QlooClient(api_key="MOCK-KEY", transport=httpx.MockTransport(handler))

    class NoSeedBrain(FakeBrain):
        async def think_json(self, prompt, session_id=None, agent="", task="", **_):
            if task == "understand":
                return {"brand_name": "Nowhere Brand", "category": "x",
                        "audience": "", "cultural_descriptors": ["obscure"],
                        "target_categories": ["music"]}
            return await super().think_json(prompt, task=task)

    result = await CollabAgent(NoSeedBrain(), qloo).run("A brand Qloo won't know.")
    assert result["candidates"] == []
    assert "no" in result["note"].lower()
