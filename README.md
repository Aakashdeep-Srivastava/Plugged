# PLUGGED

**Unexpected collabs. Cultural receipts.**

PLUGGED is an autonomous **cultural partnership intelligence** agent. Give it a
brand brief and it finds *unexpected but culturally relevant* collaboration
partners across different categories, explains the fit using **real Qloo taste
data**, separates cultural alignment from business feasibility, and drafts a
partnership proposal — which **a human approves** before anything goes out.

> Built for the Qloo Agentic Hackathon. PLUGGED builds on components of the
> open-source [Harvey](https://github.com/ethanplusai/harvey) agent (MIT) — see
> [Open-source foundation](#open-source-foundation) below.

---

## The problem

Brand collaborations are decided on gut feel and the same tired networks. The
*interesting* partner — the one whose audience genuinely overlaps yours in a way
nobody expected — is invisible to a keyword search. And when someone does propose
a collab, the "why" is a vibe, not evidence.

## What PLUGGED does

1. **Reads your brand's cultural context** from a plain-language brief.
2. **Resolves it in Qloo's taste graph** (your brand as an entity, or your
   audience's taste as tags).
3. **Explores *adjacent* categories** — music, hospitality, fashion, gaming,
   travel… — for partners Qloo reports as culturally affinitied to your audience.
   Cross-category is the point: a streetwear label × a natural-wine bar, not ×
   another streetwear label.
4. **Decides whether another Qloo query is worth it** rather than following a
   fixed script.
5. **Separates the two questions it must never conflate:**
   - **Cultural affinity** — from Qloo (the affinity number + shared tags). Evidence.
   - **Business feasibility** — PLUGGED's *own* reasoned opinion, with an explicit
     confidence level and a list of unknowns. **Not** a Qloo prediction.
6. **Ranks transparently** (by Qloo's real signal) and **drafts a concept + an
   outreach message** — held for your approval, never sent automatically.

### Why Qloo is essential

PLUGGED's core claim — "these two brands' audiences share taste" — is only
credible because it comes from Qloo's cross-domain taste graph, not from a model's
imagination. Qloo is the single source of the cultural signal: the entity
resolution, the cross-category affinity, and the shared tags that become the
"cultural receipts." Remove Qloo and PLUGGED is just opinion. Every affinity number
and tag PLUGGED shows is passed through from Qloo verbatim; nothing is invented.

**What Qloo does *not* do (and PLUGGED never claims it does):** predict purchase
behavior, campaign success, revenue, or whether a company will agree to partner.

---

## How the agent works

```
                        brand brief (text)
                              │
                   ┌──────────▼───────────┐
                   │  understand (model)   │  extract brand, audience, taste,
                   │                       │  and which categories to explore
                   └──────────┬───────────┘
                              │
                   ┌──────────▼───────────┐     Qloo  GET /search
                   │  resolve seed (Qloo)  │────────────────────────►
                   │  brand → entity, or   │     (fallback: GET /v2/tags)
                   │  taste → tag seeds    │◄────────────────────────
                   └──────────┬───────────┘
                              │
             ┌────────────────▼────────────────┐   Qloo  GET /v2/insights
             │  explore adjacent categories      │──────────────────────►
             │  + AGENT DECIDES: query again?    │   filter.type = a DIFFERENT
             │                                   │◄──  domain, seeded by the brand
             └────────────────┬──────────────────┘
                              │   candidates carry Qloo affinity + tags
                   ┌──────────▼───────────┐
                   │  analyze (model)      │  cultural rationale (cites Qloo)
                   │  — keep affinity and  │  + business feasibility (opinion,
                   │    feasibility apart  │    confidence, unknowns)
                   │  — concept + draft    │  + approval-gated outreach draft
                   └──────────┬───────────┘
                              │
                   ranked candidates  →  human approves the draft
```

- **Brain** — the reasoning model. Locally it can use your Claude Code
  subscription (inherited CLI brain) or the Anthropic API; the hosted demo uses
  the Anthropic API. Both expose the same interface, so the agent code is identical.
- **Qloo client** (`plugged/integrations/qloo.py`) — PLUGGED's original
  integration. Defensive parsing, preserves raw evidence, graceful on empty
  results / rate limits / missing keys.
- **Untrusted input** — brand briefs and any fetched text are fenced as data, not
  instructions (inherited prompt-injection defense).

---

## Key features

- Cross-category collaboration discovery grounded in Qloo affinity.
- **Evidence cards**: affinity + shared tags shown with source attribution.
- Cultural alignment and business feasibility **visibly separated**, feasibility
  shown with confidence and unknowns.
- Agent decides whether to run another Qloo query.
- Concept generator + **human-approved** outreach drafts (nothing auto-sends).
- Two front doors: a local control dashboard and a public, rate-capped web demo.

---

## Screenshots

_Placeholders — add images to `docs/screenshots/`._

- `docs/screenshots/demo-input.png` — the brand brief + "Find my next collab".
- `docs/screenshots/demo-results.png` — evidence cards with Qloo affinity.
- `docs/screenshots/dashboard-collabs.png` — the dashboard Collabs tab.

---

## Local setup

Requires **Python 3.11+**.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -e .
cp .env.example .env     # then fill in the keys below
```

### Environment variables

PLUGGED's core needs two keys (put them in `.env`, never commit it):

| Variable | Required | What it's for |
|---|---|---|
| `QLOO_API_KEY` | **yes** | Qloo Taste AI — the cultural signal. Hackathon key works only against `hackathon.api.qloo.com`. |
| `QLOO_API_BASE` | no | Override the Qloo base URL (defaults to the hackathon host). |
| `ANTHROPIC_API_KEY` | for hosting / optional locally | Model "brain" for the public demo. Locally you can instead use your Claude Code subscription CLI. |
| `ANTHROPIC_MODEL` | no | Override the model (default `claude-sonnet-5`). |

The inherited outreach pipeline (Gmail/SMTP, verifiers, etc.) has many more
optional keys — all documented inline in `.env.example` — but **none are needed**
to run PLUGGED's cultural-partnership workflow.

## How to run

**Terminal (quickest):**

```bash
plugged collab "We're a streetwear brand looking for an unexpected music, lifestyle, or hospitality collaboration."
```

**Local dashboard** (opens on the **Collabs** tab):

```bash
plugged dashboard
# open the private http://127.0.0.1:5555/#token=… link it prints
```

**Public demo locally** (the same app that deploys to Vercel):

```bash
uvicorn plugged.demo_app:app --reload
# open http://127.0.0.1:8000
```

### Demo workflow

1. Open the demo (or the dashboard Collabs tab).
2. Use the prefilled brief, or paste your own:
   *"We're a streetwear brand looking for an unexpected music, lifestyle, or
   hospitality collaboration."*
3. Press **Find my next collab** and watch the live agent activity.
4. Read the candidate **evidence cards**: Qloo affinity + shared tags (the
   receipts), the cultural rationale, and — kept separate — the business
   feasibility with its confidence and unknowns.
5. Review the generated concept and the **approval-gated** outreach draft. The
   public demo never sends anything.

---

## Deployment

The local dashboard and the Claude-subscription CLI brain are **loopback-only and
single-operator by design** — they are not safe to expose publicly (the dashboard
actively refuses non-loopback binds, and the CLI brain is tied to one person's
subscription). The public demo is therefore a **separate, stateless backend**
that calls the Anthropic API and Qloo with **server-side keys**, exposes exactly
one action, and never touches a shell, a mailbox, or local credentials.

**Vercel** (serverless Python):

```bash
npm i -g vercel
vercel            # first deploy (links the project)
# set env vars in the Vercel project (NOT in the repo):
#   QLOO_API_KEY, ANTHROPIC_API_KEY   (optional: ANTHROPIC_MODEL, DEMO_DAILY_CAP)
vercel --prod
```

- `vercel.json` routes all paths to `api/index.py` (the ASGI app) and sets
  `maxDuration` so multi-step runs don't time out.
- `api/requirements.txt` is a slim dependency set (no Playwright / mail stack).
- `.vercelignore` keeps the bundle small.
- `/api/collab` streams NDJSON so the browser shows live activity.

> Secrets live in the host's environment only. Never commit `.env`; never ship a
> key to the client.

---

## Testing

```bash
pip install -e ".[dev]"
pytest -q
```

PLUGGED's own tests live in `tests/test_qloo.py`, `tests/test_collab_agent.py`
and `tests/test_demo_app.py`. Qloo responses in tests are **clearly-labeled mock
fixtures** shaped like the real API — no network calls, and no mock affinity is
presented as a real measurement. The large inherited suite also runs.

_Note: one inherited test creates a symlink and needs symlink privilege (admin or
Developer Mode on Windows); it is an environment limitation, not a code failure._

---

## Limitations and honest claims

- **Qloo measures taste affinity, not outcomes.** PLUGGED never claims Qloo
  predicts sales, campaign success, or a partner's willingness to work with you.
- **Affinity is Qloo's; feasibility is the model's.** They are kept in separate
  fields and separately labeled in every view. Feasibility always carries a
  confidence level and explicit unknowns.
- **No invented data.** If Qloo returns no entity or no affinity, PLUGGED says so
  rather than filling a plausible-looking number.
- **Drafts are drafts.** Outreach is generated for a human to approve; the public
  demo sends nothing.
- **Demo rate-capping is best-effort** (in-memory; a serverless cold start resets
  it). A production deployment should add a platform rate limiter.
- Qloo coverage varies by brand and category; obscure brands may not resolve, in
  which case PLUGGED falls back to taste-tag seeds or reports a weak signal.

---

## Open-source foundation

PLUGGED builds on components of **Harvey** by **ethanplusai**, an MIT-licensed
autonomous sales agent. The original license and copyright notices are retained.
PLUGGED adds a Qloo-powered cultural partnership discovery and proposal workflow.

**Inherited from Harvey (MIT), reused as infrastructure:** the heartbeat/agent
framework, the model "brain" abstraction and headless Claude runtime, the SQLite
observation/signal state model, the FastAPI dashboard scaffold with its
token-gated loopback auth, the SSRF-hardened HTTP client, the prompt-injection
fencing, the outreach/mail integrations, the config system, and the Docker setup.

**Original to PLUGGED:** the Qloo integration (`plugged/integrations/qloo.py`),
the cultural-partnership agent (`plugged/collab_agent.py`), the Anthropic-API
brain (`plugged/api_brain.py`), the cultural-partnership skill, the public demo
backend and page (`plugged/demo_app.py`, `plugged/web_demo/`), the `plugged
collab` command, the Collabs dashboard tab, and the Vercel deployment.

The inherited code was **not** written from scratch for PLUGGED. See `LICENSE`
(retained) and `CHANGELOG.md` (upstream Harvey history, kept for attribution).

## License

MIT — see [`LICENSE`](LICENSE). Copyright © 2026 Ethan Rogers (Harvey), retained;
PLUGGED's additions are released under the same MIT license.
