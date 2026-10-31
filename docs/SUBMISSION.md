# PLUGGED — Devpost submission notes

**Tagline:** Unexpected collabs. Cultural receipts.

**Live demo:** https://plugged-ten.vercel.app  (runs in clearly-labeled **demo
mode**; flips to live Qloo the moment an event key is set — see "Honest status")

**Repository:** (your public GitHub URL) · **License:** MIT

---

## Elevator pitch

Sales and partnership tools know *who a company is* — industry, size, location.
They can't see *who a brand culturally belongs with*. PLUGGED adds that missing
sense. Give it a brand brief; it reads your audience's taste through **Qloo's
Taste AI**, hunts across **different** cultural categories for a surprising-but-
aligned partner, shows the **cultural receipts** (Qloo affinity + shared tags +
which seed drove the match), separates that cultural signal from a hedged
business-feasibility read, and drafts a partnership proposal — which a human
approves. It never claims Qloo predicts sales; Qloo creates the *hypothesis*,
real outreach creates the evidence.

## What it does

1. **Brand brief → cultural context.** Extracts brand, audience, taste anchors,
   and which adjacent categories to explore.
2. **Resolves the brand/taste in Qloo** (`/search`, falling back to `/v2/tags`).
3. **Cross-category discovery** via `/v2/insights` — seed the brand, set
   `filter.type` to a *different* domain (music, hospitality, lifestyle…) to find
   non-obvious partners, with `feature.explainability=true` for the "why."
4. **The agent decides** whether another Qloo query is worthwhile, rather than
   following a fixed script.
5. **Keeps two things separate, always:** cultural affinity (from Qloo, quoted as
   evidence) and business feasibility (PLUGGED's model opinion, with confidence +
   unknowns).
6. **Ranks transparently** and drafts a concept + an **approval-gated** outreach
   message. Nothing sends automatically.

## Why Qloo is essential

PLUGGED's core claim — "these two audiences share taste" — is only credible
because it comes from Qloo's cross-domain taste graph, not a model's imagination.
Qloo supplies the entity resolution, the cross-category affinity, the shared tags,
and the explainability contributors that become the on-screen "receipts." Every
affinity number and tag shown is passed through from Qloo verbatim; nothing is
invented. Remove Qloo and PLUGGED is just opinion.

## How we built it

- **Agent & infrastructure** built on the MIT-licensed **Harvey** autonomous
  agent (brain abstraction, SQLite state, FastAPI dashboard, prompt-injection
  fencing, approval outbox). PLUGGED adds the Qloo layer and the partnership
  workflow.
- **Original PLUGGED modules:** `plugged/integrations/qloo.py` (async Qloo
  client), `plugged/collab_agent.py` (the agent), `plugged/api_brain.py`
  (Anthropic-API brain for hosting), `skills/cultural_partnership.md`, the public
  demo (`plugged/demo_app.py` + page), the `plugged collab` CLI and a Collabs
  dashboard tab.
- **Deploy:** stateless FastAPI on Vercel; model via the Anthropic API,
  Qloo server-side. Keys never touch the browser.

## Honest status (please read)

Our Qloo integration is **fully implemented and wired**. Our event API key had
not been issued by submission time, so the public demo runs in a **clearly-labeled
seeded "DEMO MODE"**: it streams the complete workflow with *illustrative,
fictional* partners so judges can see every step. It is never presented as live
Qloo data. The instant a `QLOO_API_KEY` is set (locally in `.env` or as a Vercel
env var), the same flow runs against live Qloo — one variable, no code change.
We verify this with `plugged qloo test`.

## Challenges

- Keeping cultural affinity and commercial feasibility rigorously separate so the
  product never overclaims what taste data means.
- Making a single-operator, loopback-only local agent safely publicly demoable —
  solved with a separate, stateless, no-tools public backend.

## What's next

- Live Qloo across more categories and markets; market-switch comparison.
- Persisted partnership runs + a baseline-vs-Qloo evaluation.
- Human-approved outreach through the inherited, compliance-aware pipeline.

## Try it

```bash
pip install -e .
# With a Qloo key in .env:
plugged qloo test
plugged collab "We're a streetwear brand looking for an unexpected music, lifestyle, or hospitality collaboration."
plugged dashboard          # local UI (Collabs tab)
# Public demo (works even without keys, in demo mode):
uvicorn plugged.demo_app:app
```

## Built on

PLUGGED builds on components of **Harvey** by **ethanplusai** (MIT). The original
license and copyright are retained; PLUGGED adds the Qloo-powered cultural
partnership discovery and proposal workflow. See the README's "Open-source
foundation" section.
