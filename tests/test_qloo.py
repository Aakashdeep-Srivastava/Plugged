"""Tests for PLUGGED's Qloo client.

All Qloo responses here are CLEARLY-LABELED MOCK FIXTURES shaped like the
hackathon API's documented responses (docs.qloo.com). No real Qloo call is made
and no affinity number here is a real Qloo measurement — they exist only to
prove the client parses and preserves what Qloo returns.
"""

import json

import httpx
import pytest

from plugged.integrations.qloo import (
    QlooAuthError, QlooClient, QlooConfigError, QlooRateLimitError,
    resolve_entity_type,
)

# ── MOCK FIXTURES (not real Qloo data) ──────────────────────────────────────

MOCK_SEARCH = {  # shape of GET /search
    "results": [
        {
            "entity_id": "MOCK-BRAND-1",
            "name": "Aperture Coffee",
            "types": ["urn:entity:brand"],
            "popularity": 0.63,
            "properties": {"description": "A fictional specialty coffee brand."},
            "tags": [{"name": "coffee"}, {"name": "third-wave"}],
        }
    ]
}

MOCK_INSIGHTS = {  # shape of GET /v2/insights (results.entities with query.affinity)
    "results": {
        "entities": [
            {
                "entity_id": "MOCK-ARTIST-1",
                "name": "The Fictional Band",
                "types": ["urn:entity:artist"],
                "popularity": 0.71,
                "query": {"affinity": 0.88},
                "properties": {"description": "An invented indie act."},
                "tags": [{"name": "indie"}],
            },
            {
                "entity_id": "MOCK-ARTIST-2",
                "name": "Imaginary DJ",
                "types": ["urn:entity:artist"],
                "query": {"affinity": 0.54},
                "properties": {},
            },
        ]
    }
}

MOCK_TAGS = {  # shape of GET /v2/tags
    "results": {"tags": [{"tag_id": "urn:tag:genre:indie", "name": "Indie",
                          "type": "urn:tag:genre"}]}
}


def client_returning(payload, status=200):
    """A QlooClient wired to a MockTransport that always returns `payload`."""
    def handler(request):
        return httpx.Response(status, json=payload)
    return QlooClient(api_key="MOCK-KEY",
                      transport=httpx.MockTransport(handler))


# ── Tests ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_parses_entities():
    c = client_returning(MOCK_SEARCH)
    ents = await c.search("Aperture Coffee")
    assert len(ents) == 1
    e = ents[0]
    assert e.id == "MOCK-BRAND-1"
    assert e.name == "Aperture Coffee"
    assert e.entity_type == "urn:entity:brand"
    assert "coffee" in e.tags
    # search entities carry NO affinity — the client must not invent one.
    assert e.affinity is None


@pytest.mark.asyncio
async def test_insights_preserves_qloo_affinity():
    c = client_returning(MOCK_INSIGHTS)
    ents = await c.insights("music", signal_entities=["MOCK-BRAND-1"])
    assert [e.name for e in ents] == ["The Fictional Band", "Imaginary DJ"]
    # The affinity is exactly what the (mock) Qloo payload carried — not derived.
    assert ents[0].affinity == 0.88
    assert ents[1].affinity == 0.54
    # Raw evidence is preserved for the UI / audit.
    assert ents[0].raw["query"]["affinity"] == 0.88


@pytest.mark.asyncio
async def test_insights_empty_results_is_not_an_error():
    c = client_returning({"results": {"entities": []}})
    assert await c.insights("urn:entity:place", signal_tags=["urn:tag:x"]) == []


@pytest.mark.asyncio
async def test_tags_parse():
    c = client_returning(MOCK_TAGS)
    tags = await c.tags("indie")
    assert tags[0].id == "urn:tag:genre:indie"
    assert tags[0].name == "Indie"


@pytest.mark.asyncio
async def test_missing_key_raises_config_error():
    c = QlooClient(api_key="")
    with pytest.raises(QlooConfigError):
        await c.search("anything")


@pytest.mark.asyncio
async def test_auth_and_rate_limit_errors():
    with pytest.raises(QlooAuthError):
        await client_returning({"error": "nope"}, status=403).search("x")
    with pytest.raises(QlooRateLimitError):
        await client_returning({"error": "slow"}, status=429).search("x")


def test_resolve_entity_type_maps_friendly_names():
    assert resolve_entity_type("music") == "urn:entity:artist"
    assert resolve_entity_type("hospitality") == "urn:entity:place"
    assert resolve_entity_type("urn:entity:brand") == "urn:entity:brand"
    assert resolve_entity_type("not-a-category") == ""
