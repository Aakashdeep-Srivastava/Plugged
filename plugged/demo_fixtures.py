"""Seeded-demo fallback for PLUGGED.

When no Qloo key (or no model brain) is configured, the public demo still needs
to show the full workflow end to end. This module provides a CLEARLY-LABELED,
illustrative result — NOT live Qloo data.

Integrity rules (from the hackathon safe-use guidance and PLUGGED's own):
  * Every envelope is tagged mode="seeded-demo" and carries a loud note.
  * The candidate entities are FICTIONAL (invented names), so nothing here can
    be mistaken for a real Qloo result or a real business claim.
  * Affinity numbers are illustrative and labeled as such — never presented as
    real Qloo measurements.
Connect QLOO_API_KEY (+ a model brain) for genuine, live cultural evidence.
"""

SEEDED_NOTE = (
    "Demo fixture — illustrative, NOT live Qloo data. The partners and affinity "
    "numbers below are invented to show the workflow. Connect a Qloo API key "
    "(and a model brain) for real, evidence-backed cultural discovery."
)

DISCLAIMER = (
    "Affinity and tags would be reported by Qloo (taste alignment). Business "
    "feasibility is PLUGGED's model opinion, not a Qloo prediction. Qloo does not "
    "predict partnership success or revenue. Outreach drafts are held for human "
    "approval and are never sent automatically."
)

_ACTIVITY = [
    {"step": "start", "detail": "Reading the brand brief (demo fixture)"},
    {"step": "understand", "detail": "Brand: a streetwear label · exploring music, hospitality, lifestyle"},
    {"step": "resolve", "detail": "Seeded from the brief's taste (illustrative seeds)"},
    {"step": "explore", "detail": "music: 1 illustrative candidate with affinity"},
    {"step": "explore", "detail": "hospitality: 1 illustrative candidate with affinity"},
    {"step": "explore", "detail": "lifestyle: 1 illustrative candidate with affinity"},
    {"step": "rank", "detail": "3 candidates ranked by (illustrative) affinity"},
    {"step": "done", "detail": "3 partnership candidates ready for review (demo)"},
]

_CANDIDATES = [
    {
        "id": "DEMO-ARTIST-1", "name": "Neon Hours", "category": "music",
        "entity_type": "urn:entity:artist",
        "qloo_affinity": 0.89, "qloo_popularity": 0.6,
        "qloo_tags": ["indie electronic", "late-night", "DIY scene", "warehouse"],
        "qloo_contributors": [{"entity_id": "DEMO-SEED-1", "influence": 0.64},
                              {"entity_id": "DEMO-SEED-2", "influence": 0.31}],
        "cultural_rationale": "Shares your audience's late-night, DIY-scene taste "
            "(warehouse / indie-electronic tags) — a music world your wearers already live in.",
        "business_feasibility": {
            "assessment": "A capsule drop timed to a tour is low-lift and on-brand; "
                "an emerging act is usually reachable without an agency gatekeeper.",
            "confidence": "medium",
            "unknowns": ["tour schedule overlap", "label merch exclusivity", "budget"],
        },
        "concept": "A limited tour-capsule: a 20-piece run sold only at shows and your "
            "drop, with a B-side exclusive to buyers.",
        "outreach_draft": "Hey — we keep seeing the same crowd at your shows and in our "
            "drops. We'd love to do a tiny tour-capsule with you: 20 pieces, show-only, "
            "a track for buyers. Open to a quick call?",
        "approval_required": True,
    },
    {
        "id": "DEMO-PLACE-1", "name": "Café Transistor", "category": "hospitality",
        "entity_type": "urn:entity:place",
        "qloo_affinity": 0.81, "qloo_popularity": 0.52,
        "qloo_tags": ["listening bar", "natural wine", "vinyl", "design-forward"],
        "qloo_contributors": [{"entity_id": "DEMO-SEED-1", "influence": 0.58}],
        "cultural_rationale": "A listening-bar / vinyl / design-forward profile overlaps "
            "your audience's taste off the street and into a room they'd actually hang in.",
        "business_feasibility": {
            "assessment": "A pop-up / in-store event is a classic, cheap activation; "
                "single-venue so logistics are simple.",
            "confidence": "medium",
            "unknowns": ["venue capacity", "date availability", "local footfall"],
        },
        "concept": "A one-night 'open the drop' listening party at the bar: your capsule, "
            "their records, a co-designed coaster as the ticket.",
        "outreach_draft": "Hi — your room is exactly where our people already spend their "
            "nights. Could we host a one-night listening party around our next drop? "
            "Happy to co-design a little keepsake for it.",
        "approval_required": True,
    },
    {
        "id": "DEMO-BRAND-1", "name": "Riso & Rye", "category": "lifestyle",
        "entity_type": "urn:entity:brand",
        "qloo_affinity": 0.74, "qloo_popularity": 0.41,
        "qloo_tags": ["risograph", "zine culture", "indie print", "limited runs"],
        "qloo_contributors": [{"entity_id": "DEMO-SEED-2", "influence": 0.49}],
        "cultural_rationale": "Zine / risograph / limited-run culture mirrors the "
            "collectible, small-batch instinct your drops run on.",
        "business_feasibility": {
            "assessment": "Co-produced print goods are inexpensive and shippable; good "
                "low-risk first collab if the music/venue ones stall.",
            "confidence": "low",
            "unknowns": ["print lead times", "margin split", "whether they do apparel inserts"],
        },
        "concept": "",
        "outreach_draft": "",
        "approval_required": True,
    },
]


def seeded_demo_result(brief: str = "") -> dict:
    """A full, clearly-labeled demo result envelope (mode='seeded-demo')."""
    return {
        "mode": "seeded-demo",
        "brand_context": {
            "brand_name": "", "category": "streetwear",
            "audience": "young, scene-driven, collectible-minded",
            "cultural_descriptors": ["DIY", "late-night", "design-led"],
            "target_categories": ["music", "hospitality", "lifestyle"],
        },
        "qloo_queries": [{"endpoint": "(demo fixture)", "note": "no live Qloo call made"}],
        "candidates": [dict(c) for c in _CANDIDATES],
        "activity": [dict(e) for e in _ACTIVITY],
        "note": SEEDED_NOTE,
        "disclaimer": DISCLAIMER,
    }


def seeded_demo_events() -> list[dict]:
    """The synthetic activity events to stream before the result."""
    return [dict(e) for e in _ACTIVITY]
