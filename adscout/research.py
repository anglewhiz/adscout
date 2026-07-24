"""Keyword-research mode: a reusable, downstream-agent-ready JSON research object.

When the user asks for keyword / niche research, the analyst switches from the
normal Markdown verdict to emitting a structured research object grounded in the
SpyFu keyword data and enriched by the strategy/playbook lenses. The object is
vendor-agnostic so it can be piped straight into Make/Airtable/Sheets or fed to
downstream agents (avatar, offer, SEO, PPC, content, VSL).
"""

from __future__ import annotations

import json
import re

# The exact shape the model must return. Data fields come from the SpyFu tools;
# strategy/customer fields are inferred from that data + marketing expertise.
RESEARCH_INSTRUCTIONS = """\
KEYWORD-RESEARCH MODE — the user wants keyword/niche research, so IGNORE the
standard "## Answer / ## Evidence / ## Verdict" format above. Instead:

1. Gather real data first. Call research_keywords across several search types
   (PhraseMatch, Questions, Transactions, AlsoBuysAdsFor) and
   find_advertisers_for_topic for the niche, to collect keywords with search
   volume, CPC, and advertiser/competitor counts. Optionally get_keyword_ad_history
   for a couple of the strongest terms.
2. Apply the frameworks: score each candidate on the four-part filter (meaningful
   volume, strong RELEVANCE as a causal/emotional reframe not a demographic slice,
   bid price/CPC, advertiser competition). Favour lower-volume, higher-intent
   "underbelly" sub-niches over contested head terms. Separate local/commercial
   intent from informational. Map searcher statements -> keyword -> funnel stage
   -> best asset.
3. Return ONLY a single JSON object in a ```json fenced block, no prose outside
   it, matching this schema exactly (fill every field you can; use null or [] when
   genuinely unknown; NEVER invent SpyFu numbers you didn't retrieve):

```json
{
  "research_summary": {
    "niche": "",
    "research_method": "Livingston underbelly + intent-based keyword research",
    "criteria": ["meaningful volume","relevance (causal/emotional reframe)","commercial value (CPC)","advertiser competition","search intent","local vs informational"],
    "total_keywords": 0,
    "data_source": "SpyFu (Google Search)",
    "generated_at": ""
  },
  "market_summary": {
    "top_opportunity": "",
    "reason": "",
    "positioning_angle": "",
    "overall_recommendation": "",
    "market_score": 0
  },
  "keyword_opportunities": [
    {"priority": 1, "keyword": "", "monthly_volume": 0, "cpc": null, "paid_competitors": 0, "difficulty": null, "search_intent": "", "funnel_stage": "TOFU|MOFU|BOFU", "opportunity_score": 0, "recommendation": "", "notes": ""}
  ],
  "secondary_opportunities": [
    {"keyword": "", "why_it_matters": "", "best_use_case": ""}
  ],
  "avoid_keywords": [
    {"keyword": "", "reason": ""}
  ],
  "keyword_clusters": [
    {"cluster": "", "primary_keyword": "", "supporting_keywords": [], "intent": "", "recommended_page": ""}
  ],
  "customer_problems": [],
  "customer_desires": [],
  "customer_objections": [],
  "content_opportunities": [
    {"searcher_problem": "", "target_keyword": "", "funnel_stage": "", "recommended_asset": "", "recommended_cta": ""}
  ],
  "offer_opportunities": [],
  "competitor_gaps": [],
  "ppc_strategy": {"campaigns": [], "notes": []},
  "seo_strategy": {"clusters": [], "notes": []},
  "next_actions": [
    {"priority": 1, "task": "", "reason": ""}
  ],
  "confidence_score": 0.0
}
```

Field notes: opportunity_score and market_score are 0-100 (your weighting of
volume vs competition vs intent vs differentiation); confidence_score is 0-1
(how much real data backed the object). funnel_stage is TOFU/MOFU/BOFU. Keep
keyword_opportunities to the ~12 strongest, ranked by priority. Keep every
string to one concise sentence and RETURN THE COMPLETE JSON OBJECT — do not let
it truncate; trim depth before you sacrifice valid, closed JSON."""


def extract_research(text: str) -> dict | None:
    """Pull the JSON research object out of the model's answer, or None."""
    if not text:
        return None
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    candidate = m.group(1) if m else None
    if candidate is None:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text[start:end + 1]
    if not candidate:
        return None
    try:
        obj = json.loads(candidate)
    except (ValueError, TypeError):
        return None
    return obj if isinstance(obj, dict) else None
