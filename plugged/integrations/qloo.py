"""Qloo Taste AI client — PLUGGED's cultural intelligence source.

This is PLUGGED's original integration (not inherited from Harvey). It talks to
the Qloo hackathon API and returns *only* what Qloo actually sends back:
entities, their tags, and the affinity Qloo reports. Nothing here invents an
affinity score, a partnership, or a business fact — missing data stays missing.

Endpoints used (hackathon API, see docs.qloo.com):
  GET /search            resolve a name (a brand, artist, place...) -> entity IDs
  GET /v2/insights       given seed entities/tags, return affinitied entities
                         in a chosen category (filter.type) — the cross-category
                         engine behind "unexpected collabs"
  GET /v2/tags           resolve a keyword -> tag IDs

Auth is the ``X-Api-Key`` header. The key is valid only against the hackathon
base URL. Params that don't apply to a given ``filter.type`` are silently
ignored by Qloo and usually surface as empty results, so callers must treat an
empty list as "no signal", never as an error.
"""

import logging
import os

import httpx

logger = logging.getLogger("plugged.qloo")

DEFAULT_BASE_URL = "https://hackathon.api.qloo.com"
DEFAULT_TIMEOUT = 20.0

# The entity types the hackathon Insights API supports as filter.type values.
ENTITY_TYPES = (
    "urn:entity:artist",
    "urn:entity:book",
    "urn:entity:brand",
    "urn:entity:destination",
    "urn:entity:movie",
    "urn:entity:person",
    "urn:entity:place",
    "urn:entity:podcast",
    "urn:entity:tv_show",
    "urn:entity:video_game",
)

# Friendly category names PLUGGED uses internally -> Qloo entity-type URNs.
# "music" is artist, "hospitality"/"dining" is place, "lifestyle" is brand, etc.
CATEGORY_TO_URN = {
    "artist": "urn:entity:artist",
    "music": "urn:entity:artist",
    "book": "urn:entity:book",
    "brand": "urn:entity:brand",
    "lifestyle": "urn:entity:brand",
    "fashion": "urn:entity:brand",
    "destination": "urn:entity:destination",
    "travel": "urn:entity:destination",
    "movie": "urn:entity:movie",
    "film": "urn:entity:movie",
    "person": "urn:entity:person",
    "place": "urn:entity:place",
    "hospitality": "urn:entity:place",
    "dining": "urn:entity:place",
    "podcast": "urn:entity:podcast",
    "tv_show": "urn:entity:tv_show",
    "tv": "urn:entity:tv_show",
    "video_game": "urn:entity:video_game",
    "gaming": "urn:entity:video_game",
}


def resolve_entity_type(name: str) -> str:
    """A friendly category name -> a Qloo entity-type URN (``""`` if unknown).

    Accepts an already-qualified ``urn:entity:...`` unchanged.
    """
    n = (name or "").strip().lower()
    if n.startswith("urn:entity:"):
        return n if n in ENTITY_TYPES else ""
    return CATEGORY_TO_URN.get(n, "")


# ── Errors ────────────────────────────────────────────────────────────────


class QlooError(Exception):
    """Any failure talking to Qloo."""


class QlooConfigError(QlooError):
    """No API key configured — nothing was called."""


class QlooAuthError(QlooError):
    """Qloo rejected the key (401/403)."""


class QlooRateLimitError(QlooError):
    """Qloo returned 429 — the plan's rate/quota limit was hit."""


# ── Result shapes (raw evidence is always preserved) ────────────────────────


class QlooEntity:
    """One entity Qloo returned, keeping the raw payload as evidence.

    ``affinity`` is populated ONLY when Qloo includes it (insights results carry
    ``query.affinity``, a 0-1 relevance Qloo computed for the seed); it is None
    on plain search results. PLUGGED never fills this in itself.
    """

    __slots__ = ("id", "name", "types", "entity_type", "affinity",
                 "popularity", "tags", "properties", "raw")

    def __init__(self, data: dict):
        self.raw = data if isinstance(data, dict) else {}
        self.id = str(self.raw.get("entity_id") or self.raw.get("id") or "")
        self.name = str(self.raw.get("name") or "")
        types = self.raw.get("types") or self.raw.get("type") or []
        self.types = [types] if isinstance(types, str) else list(types)
        self.entity_type = self.types[0] if self.types else ""
        self.affinity = _affinity_of(self.raw)
        pop = self.raw.get("popularity")
        self.popularity = float(pop) if isinstance(pop, (int, float)) else None
        self.tags = _tag_names(self.raw.get("tags"))
        self.properties = self.raw.get("properties") if isinstance(
            self.raw.get("properties"), dict) else {}

    @property
    def description(self) -> str:
        return str(self.properties.get("description") or
                   self.properties.get("short_description") or "")

    @property
    def image(self) -> str:
        img = self.properties.get("image")
        if isinstance(img, dict):
            return str(img.get("url") or "")
        return str(img or "")

    def summary(self) -> dict:
        """A compact, JSON-safe view for prompts and the dashboard."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.entity_type,
            "affinity": self.affinity,
            "popularity": self.popularity,
            "tags": self.tags[:8],
            "description": self.description[:280],
        }


class QlooTag:
    __slots__ = ("id", "name", "type", "raw")

    def __init__(self, data: dict):
        self.raw = data if isinstance(data, dict) else {}
        self.id = str(self.raw.get("tag_id") or self.raw.get("id") or "")
        self.name = str(self.raw.get("name") or "")
        self.type = str(self.raw.get("type") or self.raw.get("subtype") or "")


def _affinity_of(entity: dict) -> float | None:
    """Qloo's reported affinity for an insights entity, or None.

    Insights entities carry ``query.affinity`` (0-1). A few payload variants put
    it at ``affinity`` directly. Returns None when Qloo gave none — never a guess.
    """
    q = entity.get("query")
    if isinstance(q, dict) and isinstance(q.get("affinity"), (int, float)):
        return float(q["affinity"])
    if isinstance(entity.get("affinity"), (int, float)):
        return float(entity["affinity"])
    return None


def _tag_names(tags) -> list[str]:
    out = []
    if isinstance(tags, list):
        for t in tags:
            if isinstance(t, dict) and t.get("name"):
                out.append(str(t["name"]))
            elif isinstance(t, str):
                out.append(t)
    return out


def _entities_from(data: dict) -> list[dict]:
    """Pull the entity list out of a Qloo response, tolerating both the
    ``{"results": {"entities": [...]}}`` and ``{"results": [...]}`` shapes."""
    results = data.get("results") if isinstance(data, dict) else None
    if isinstance(results, dict):
        for key in ("entities", "entity"):
            if isinstance(results.get(key), list):
                return results[key]
        return []
    if isinstance(results, list):
        return results
    return []


def _tags_from(data: dict) -> list[dict]:
    results = data.get("results") if isinstance(data, dict) else None
    if isinstance(results, dict) and isinstance(results.get("tags"), list):
        return results["tags"]
    if isinstance(results, list):
        return results
    return []


# ── Client ──────────────────────────────────────────────────────────────────


class QlooClient:
    """Async Qloo client. One instance per request is fine; it holds no state."""

    def __init__(self, api_key: str = "", base_url: str = "",
                 timeout: float = DEFAULT_TIMEOUT, transport=None):
        self.api_key = (api_key or os.getenv("QLOO_API_KEY", "")).strip()
        self.base_url = (base_url or os.getenv("QLOO_API_BASE", "")
                         or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        # Tests inject an httpx.MockTransport here; production leaves it None.
        self._transport = transport

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    async def _get(self, path: str, params: dict) -> dict:
        if not self.api_key:
            raise QlooConfigError(
                "QLOO_API_KEY is not set. Add it to .env — the hackathon key "
                "works only against " + DEFAULT_BASE_URL + ".")
        # Drop None/empty params so Qloo isn't sent blanks.
        clean = {k: v for k, v in params.items() if v not in (None, "", [])}
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout,
                                         transport=self._transport) as client:
                resp = await client.get(
                    url, params=clean, headers={"X-Api-Key": self.api_key,
                                                "Accept": "application/json"})
        except httpx.HTTPError as e:
            raise QlooError(f"Could not reach Qloo ({type(e).__name__}).") from e
        if resp.status_code in (401, 403):
            raise QlooAuthError("Qloo rejected the API key (check QLOO_API_KEY "
                                "and that it's a hackathon key).")
        if resp.status_code == 429:
            raise QlooRateLimitError("Qloo rate/quota limit reached. Slow down "
                                     "or ask for a higher limit in Discord.")
        if resp.status_code >= 400:
            raise QlooError(f"Qloo returned {resp.status_code}: "
                            f"{resp.text[:200]}")
        try:
            data = resp.json()
        except ValueError as e:
            raise QlooError("Qloo returned a non-JSON response.") from e
        return data if isinstance(data, dict) else {"results": data}

    async def search(self, query: str, types: str = "", take: int = 10
                     ) -> list[QlooEntity]:
        """Resolve a free-text name to Qloo entities. ``types`` optionally
        narrows to one or more entity-type URNs (comma-separated)."""
        if not (query or "").strip():
            return []
        data = await self._get("/search", {
            "query": query.strip(),
            "types": types,
            "take": take,
        })
        return [QlooEntity(e) for e in _entities_from(data) if isinstance(e, dict)]

    async def tags(self, query: str, types: str = "", take: int = 20
                   ) -> list[QlooTag]:
        """Find Qloo tag IDs by keyword (there is no static tag list)."""
        if not (query or "").strip():
            return []
        data = await self._get("/v2/tags", {
            "filter.query": query.strip(),
            "filter.tag.types": types,
            "take": take,
        })
        return [QlooTag(t) for t in _tags_from(data) if isinstance(t, dict)]

    async def insights(
        self,
        filter_type: str,
        signal_entities: list[str] | None = None,
        signal_tags: list[str] | None = None,
        filter_tags: list[str] | None = None,
        take: int = 20,
        extra_params: dict | None = None,
    ) -> list[QlooEntity]:
        """The cross-category engine: entities in ``filter_type`` that Qloo
        reports as affinitied to the given seed entities/tags.

        ``filter_type`` is a Qloo entity-type URN or a friendly name
        (``resolve_entity_type`` maps "music" -> ``urn:entity:artist`` etc.).
        Returns entities carrying Qloo's ``affinity``; an empty list means Qloo
        found no signal (often because a param doesn't apply to this type).
        """
        urn = resolve_entity_type(filter_type) or filter_type
        params = {
            "filter.type": urn,
            "signal.interests.entities": ",".join(signal_entities or []),
            "signal.interests.tags": ",".join(signal_tags or []),
            "filter.tags": ",".join(filter_tags or []),
            "take": take,
        }
        if extra_params:
            params.update(extra_params)
        data = await self._get("/v2/insights", params)
        return [QlooEntity(e) for e in _entities_from(data) if isinstance(e, dict)]
