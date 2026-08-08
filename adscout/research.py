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
   -> best asset. Additional heuristics: highly specific queries (model numbers,
   SKUs, exact attributes) signal a buyer with card in hand — flag them even at
   tiny volume; manufacture long-tail coverage by multiplying shopping modifiers
   (buy, best, compare, near me, pricing, reviews) across head terms, brands and
   product types; when two candidates tie, prefer the BOFU variant; rising-volume
   momentum beats absolute volume for entry timing; a supporting keyword with its
   own long tail can be promoted to pillar of a second cluster. For content and
   lead-magnet recommendations favour tools, templates, checklists and swipe files
   (fast to consume, high perceived value) over long-form assets, and name the
   ascension step — what the asset should sell next.
   MARKET-FLIPPER PASS: classify every keyword by role — "entry" (high volume,
   low CPC, names a life moment/hobby/curiosity: the door), "money" (lower
   volume, $5-50+ CPC, names an imminent purchase: the invoice), or "bridge"
   (comparison/review terms between them). Then hunt entry->money PAIRS: the
   same searcher days apart (puppy names -> pet insurance for puppies). Check
   the four money lanes for the niche — insurance, big-ticket services,
   SaaS/subscriptions, financial products — and apply the viability rule: if no
   adjacent money lane clears ~$5-10 CPC, flag the niche as flip-unviable no
   matter the volume. For each flip pair name the bridge asset (calculator /
   generator / checklist / glossary — something genuinely useful at the entry
   moment) and its EMAIL-CAPTURE mechanism: the goal is not a Tuesday sale but
   permission to be present on Saturday. Run get_keyword_ad_history on the top
   money keywords — long-running advertisers reveal which offers profitably pay
   those CPCs; never recommend a money page without naming who currently pays.
3. Return ONLY a single JSON object in a ```json fenced block, no prose outside
   it, matching this schema exactly (fill every field you can; use null or [] when
   genuinely unknown; NEVER invent SpyFu numbers you didn't retrieve):

```json
{
  "research_summary": {
    "niche": "",
    "research_method": "Livingston underbelly + intent-based keyword research + market-flipper entry/money mapping",
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
    {"priority": 1, "keyword": "", "monthly_volume": 0, "cpc": null, "paid_competitors": 0, "difficulty": null, "search_intent": "", "funnel_stage": "TOFU|MOFU|BOFU", "keyword_role": "entry|bridge|money", "opportunity_score": 0, "recommendation": "", "notes": ""}
  ],
  "market_flip": {
    "flip_viability": "viable|marginal|unviable",
    "viability_reason": "",
    "money_lanes": [
      {"lane": "insurance|big_ticket_service|saas_subscription|financial_product", "keywords": [], "cpc_range": "", "who_pays": ""}
    ],
    "flip_pairs": [
      {"entry_keyword": "", "entry_volume": 0, "entry_cpc": null, "money_keyword": "", "money_volume": 0, "money_cpc": null, "bridge_asset": "", "capture_mechanism": "", "intent_timeline": ""}
    ],
    "content_pyramid": {
      "base_traffic": [],
      "middle_trust": [],
      "top_money": [],
      "note": "money pages are fed by internal links + email follow-up from the base layer, never by cold SERP traffic"
    }
  },
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
    {"searcher_problem": "", "target_keyword": "", "funnel_stage": "", "recommended_asset": "", "framework": "", "outline": [], "bridge": "", "recommended_cta": ""}
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
keyword_opportunities to the ~12 strongest, ranked by priority. keyword_role is
the flipper classification (entry = cheap door, money = expensive invoice,
bridge = the comparison/review terms between). market_flip is the heart of the
flip read: flip_pairs pair an entry keyword with the money keyword the SAME
searcher types days later — bridge_asset names a buildable giveaway (calculator,
generator, checklist, glossary), capture_mechanism names the email hook, and
intent_timeline states the life-moment gap in plain words ("names the puppy
Tuesday, insures it Saturday"). money_lanes.who_pays names the long-running
advertisers found via ad history — real CPC payers, not guesses. The
content_pyramid maps keywords/pages to base (traffic), middle (trust), top
(money); if no lane clears ~$5-10 CPC set flip_viability to "unviable" and say
why in viability_reason rather than forcing pairs.
keyword_clusters[].recommended_page MUST be one of the 15 landing-page slugs or
a blog-framework slug from the CONTENT-FRAMEWORK CATALOG below, chosen by the
cluster's intent and funnel stage. In content_opportunities[]:
recommended_asset MUST name a framework slug from that catalog; "framework"
repeats the slug; "outline" is an array of 4-8 section strings taken from that
framework's section order, each adapted to the target keyword (not the generic
labels); "bridge" names the landing-page slug this content should feed plus the
bridge asset (e.g. "steps — the step-by-step checklist"), per the blog->landing
pairing table. Keep every string to one concise sentence and RETURN THE
COMPLETE JSON OBJECT — do not let it truncate; trim depth before you sacrifice
valid, closed JSON."""


def extract_research(text: str) -> dict | None:
    """Pull the JSON research object out of the model's answer, or None."""
    if not text:
        return None
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    candidate = m.group(1) if m else None
    if candidate is None:
        # No closed fence — grab from the first "{" to the last "}" OR to the
        # end of the text (a max_tokens cut-off leaves no closing brace at all).
        start = text.find("{")
        if start != -1:
            end = text.rfind("}")
            candidate = text[start:end + 1] if end > start else text[start:]
    if not candidate:
        return None
    try:
        obj = json.loads(candidate)
    except (ValueError, TypeError):
        obj = _repair_truncated(candidate)
        if obj is not None:
            obj["recovered_from_truncation"] = True
    return obj if isinstance(obj, dict) else None


def _repair_truncated(candidate: str) -> dict | None:
    """Best-effort recovery of a research object cut off mid-stream.

    When the model hits max_tokens the JSON stops mid-value; rather than lose
    the whole report, trim back to the last complete fragment and close every
    open string/array/object. Returns None if nothing parseable survives.
    """
    s = candidate.strip()
    for _ in range(500):
        s = s.rstrip()
        if len(s) < 2 or s[0] != "{":
            return None
        # scan once: track open brackets and whether we end inside a string
        stack, in_str, esc = [], False, False
        for ch in s:
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
            elif ch == '"':
                in_str = True
            elif ch in "{[":
                stack.append(ch)
            elif ch in "}]":
                if stack:
                    stack.pop()
        attempt = (s + '"') if in_str else s
        attempt = attempt.rstrip()
        if attempt.endswith((",", ":")):
            s = attempt[:-1]
            continue
        closers = "".join("}" if c == "{" else "]" for c in reversed(stack))
        try:
            obj = json.loads(attempt + closers)
            return obj if isinstance(obj, dict) else None
        except (ValueError, TypeError):
            cut = max(s.rfind(","), s.rfind("{"), s.rfind("["))
            if cut <= 0:
                return None
            s = s[:cut]
    return None
