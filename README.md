# AdScout

Ask marketing questions in plain English; get answers **proven or disproven with
real competitive-intelligence data**.

```
$ adscout ask "How are people running ads in the dog food niche?" --trace

The dog-food PPC space is dominated by a few well-funded advertisers...
chewy.com runs the widest coverage (est. $812K/mo ad budget, 5,871 paid keywords),
with ad copy leaning on "free 1-2 day shipping" and "autoship & save". Challenger
brands (thefarmersdog.com, ollie.com) compete on "fresh/human-grade" angles and
aggressive trial offers (50% off)...

VERDICT: SUPPORTED — the niche is actively and heavily advertised.
Key numbers: 18 distinct advertisers on "best dog food"; top CPC ~$3.10 on
"dog food delivery"; chewy.com avg ad rank 1.4.

--- evidence trace ---
1. find_advertisers_for_topic({'topic': 'dog food'}) -> 3 rows of ~812 total
2. get_keyword_ad_history({'keyword': 'best dog food'}) -> 2 rows
3. get_domain_stats({'domain': 'chewy.com'}) -> 1 rows
```

> **Not affiliated with, endorsed by, or sponsored by SpyFu.** AdScout is an
> independent tool that can query the SpyFu API as one competitive-intelligence
> data provider. "SpyFu" is a trademark of its respective owner and is used here
> only to describe that integration.

## How it works

```
   your question
        │
        ▼
  ┌───────────┐   tool calls    ┌──────────────┐   HTTPS    ┌──────────────────┐
  │  Analyst  │ ──────────────► │    Client    │ ─────────► │  data provider   │
  │  (Claude  │ ◄────────────── │  (auth,retry │ ◄───────── │  (SpyFu API)     │
  │ tool-use) │   JSON results  │  pagination) │            └──────────────────┘
  └───────────┘                 └──────────────┘
        │
        ▼
  grounded answer + evidence trace
```

Claude is given a set of marketing-oriented **tools** (find advertisers, pull ad
copy, size up a domain's spend, map competitors). It decides which to call for a
given question, the client executes them against the data provider, results are
fed back, and Claude synthesizes a verdict that cites concrete numbers. Every
call is logged to a trace so the reasoning is auditable.

## Web UI

A browser frontend is included. Run it locally with zero extra dependencies:

```bash
python server.py            # then open http://localhost:8000
```

Type a question, pick a **mode**, and hit *Analyze*. The answer highlights the
verdict and shows the full evidence trace (every tool call + result). Modes:

| Mode       | Data      | Claude reasoning | Keys required |
|------------|-----------|------------------|---------------|
| **Demo**   | sample    | scripted         | none — fully offline |
| **Mock**   | sample    | real Claude      | `ANTHROPIC_API_KEY` |
| **Live**   | real API  | real Claude      | provider creds + `ANTHROPIC_API_KEY` |

Modes you don't have keys for are disabled automatically, so a keyless deploy
lands cleanly on **Demo**. `PORT` and `HOST` env vars override the local
defaults (`8000` / `127.0.0.1`).

## Deploy to Vercel

The repo is Vercel-ready: the frontend is static (`public/index.html`) and the
API is two Python serverless functions (`api/ask.py`, `api/status.py`).

1. Push this repo to GitHub.
2. In Vercel → **Add New… → Project**, import the GitHub repo. Framework preset:
   **Other** (no build step needed).
3. **Deploy.** The site comes up in **Demo** mode with no keys — fully usable.

To enable the AI-backed modes, add environment variables in **Vercel → Project →
Settings → Environment Variables**, then redeploy:

- `ANTHROPIC_API_KEY` — enables **Mock** mode (real Claude over sample data).
- `SPYFU_API_ID` + `SPYFU_SECRET_KEY` — additionally enables **Live** mode.

> ⚠️ **Cost/abuse note:** any environment key set on a *public* deployment can be
> used by anyone who visits the site, spending your API credit. For a public URL,
> either leave keys unset (Demo-only) or put the deployment behind Vercel access
> protection / your own auth before adding keys.

Serverless timeout is set to 60s in `vercel.json` (Live/Mock can take 10–30s;
Demo is instant).

## Setup (local, for AI modes)

```bash
pip install -r requirements.txt        # or: pip install -e .
cp .env.example .env                    # then fill in your keys
```

Credentials:

- **Anthropic** — `ANTHROPIC_API_KEY`, for AdScout's reasoning loop (Mock + Live).
- **Data provider (SpyFu)** — `SPYFU_API_ID` + `SPYFU_SECRET_KEY`, found under
  *Account Settings → API Usage* on spyfu.com. API access requires a Pro + AI or
  Team/Agency plan. (Live mode only.)

## Usage (CLI)

```bash
adscout ask "who advertises on grain free dog food and what offers do they use?"
adscout ask "is anyone spending big on 'meal kit' ads?" --country US --trace
adscout ask "map chewy.com's paid competitors" --max-steps 4
```

Or from Python:

```python
from adscout import Analyst, SpyFuClient, Settings

settings = Settings.load()
with SpyFuClient(settings) as client:
    result = Analyst(client, model=settings.model).ask(
        "How are people running ads in the dog food niche?"
    )
print(result.answer)
for call in result.trace:
    print(call.name, call.input, "->", call.result_summary)
```

## Verified provider endpoints

These were confirmed against SpyFu's OpenAPI specs. The **server segment is not
guessable** from the docs URL (e.g. ad history lives under `cloud_ad_history_api`),
which is why each is stored explicitly in `adscout/endpoints.py`.

| Tool (Claude-facing)          | Endpoint                                                 | Key params |
|-------------------------------|----------------------------------------------------------|------------|
| `find_advertisers_for_topic`  | `apis/keyword_api/v2/related/getKeywordExpansions`       | query, keywordSearchType=AlsoBuysAdsFor |
| `research_keywords`           | `apis/keyword_api/v2/related/getKeywordExpansions`       | query, keywordSearchType |
| `get_keyword_ad_history`      | `apis/cloud_ad_history_api/v2/term/getTermAdHistory`     | term |
| `get_domain_ads`              | `apis/serp_api/v2/ppc/getPaidSerps`                      | query (domain) |
| `get_top_ppc_competitors`     | `apis/competitors_api/v2/ppc/getTopCompetitors`         | domain |
| `get_domain_stats`            | `apis/domain_stats_api/v2/getLatestDomainStats`         | domain, pastNMonths |
| (also wired) full history     | `apis/domain_stats_api/v2/getAllDomainStats`            | domain |

Auth is HTTP Basic: Base64 of `SPYFU_API_ID:SECRET_KEY` in the `Authorization`
header.

## Adding more endpoints

To add one:

1. Open its page on `developer.spyfu.com`, then append `.md` to the URL to get the
   raw OpenAPI (e.g. `.../reference/toppagesapi_gettoppages_get.md`).
2. Copy `servers[0].url` → `server` and the path key → `path` into a new
   `Endpoint(...)` in `adscout/endpoints.py`.
3. Add a curated tool schema + a `dispatch` branch in `adscout/tools.py`.

## Testing

```bash
python tests/test_offline.py        # no network / no credentials needed
```

The suite exercises URL construction, param handling, and the **full
orchestration loop** using a scripted fake Claude and sample data.

## Limitations & notes

- Provider metrics (ad budget, clicks, CPC) are **estimates**, and default to the
  US market unless a market is set. The analyst is instructed to flag this.
- The provider enforces rate limits and pay-as-you-go pricing; the client retries
  on 429 and honors `Retry-After`, but heavy pagination consumes API credit.
- This tool answers competitive-intelligence questions; it is not financial or
  legal advice.
