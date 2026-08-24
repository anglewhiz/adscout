"""Affiliate-offer scouting mode: evidence-first offer vetting for paid traffic.

When the user asks which affiliate offer to promote (ClickBank/Digistore/etc.
plus a traffic source), the analyst swaps the verdict format for a structured
offer-scouting report. Principle: marketplace popularity metrics (Gravity and
kin) measure affiliate CROWDING, not opportunity — the report ranks offers by
ad-library receipts, payout-ceiling economics, and traffic-source fit, and
fixes the kill/scale rules BEFORE any spend, mirroring the validator's
stop/continue discipline.
"""

from __future__ import annotations

OFFERS_INSTRUCTIONS = """\
AFFILIATE-OFFER SCOUTING MODE — the user wants to pick an affiliate offer to
promote with paid traffic, so IGNORE the standard "## Answer / ## Evidence /
## Verdict" format. Instead:

1. Establish candidates. You CANNOT browse affiliate marketplaces — marketplace
   stats (Gravity, listed avg payout) are usable only if the user supplied them;
   otherwise record them as null with payout_source "unverified", never guessed.
   Candidates come from the user's list, or are discovered from the market
   itself: search_facebook_ads on the niche (who runs volume?), then
   find_advertisers_for_topic / get_keyword_ad_history for the Google side.
2. Verify real market activity per candidate — activity receipts, not
   popularity: search_facebook_ads / get_advertiser_facebook_ads by product and
   brand name (count of ACTIVE ads, count of DISTINCT advertiser pages, oldest
   still-running ad); get_keyword_ad_history on the offer's money terms (who
   has paid those CPCs, for how long). Many distinct advertisers running one
   offer for months = the market saying the payout supports traffic costs; a
   single advertiser (usually the vendor) = affiliate demand NOT proven. For
   physical products, search_tiktok_shop is a demand receipt (units x price).
   extract_product_page on the vendor's sales/pricing page for the real offer
   structure; at most 1-2 capture_landing_page calls on the funnel or a rival's
   presell. Never confuse advertising ACTIVITY with advertising PROFITABILITY —
   long runtimes are the best available proxy, not proof; say so in the report.
   BE ECONOMICAL — the whole analysis must fit one serverless run: spend at
   most ~3 slow calls total (Meta lookups / extract_product_page /
   capture_landing_page combined). With a candidate list, rank candidates by
   the fast SpyFu read first and spend the slow budget on the top 2-3 only.
   With NO candidate list (discovery), do ONE niche-level search_facebook_ads
   sweep plus fast SpyFu calls to shortlist, verify at most the top 1-2 names,
   and return the rest as tier C with null ad_evidence and their verification
   queued in validation_plan day 1 — a delivered shortlist beats a timed-out
   deep dive. Skip screenshots in discovery runs.
3. Run the payout-ceiling economics. The affiliate's entire LTV is the payout:
   no back-end rescues thin front-end math. Break-even CPA = average payout
   (use AVERAGE payout with upsells/rebills when known, not front-end
   commission); break-even CPC = EPC = payout x funnel conversion rate. Model
   conservative / base / optimistic CVR scenarios, all labeled as ESTIMATES
   with the assumed range stated — never present them as knowns. Size the test:
   budget should cover ~3x average payout of spend before a verdict; the
   per-ad kill rule fires at roughly ONE payout spent with no sale (kill the
   AD and replace the creative, not the campaign).
4. Autopsy the backend — the offer is a monetization ecosystem, not a product.
   Two backends exist and they are scored separately:
   - The VENDOR's backend: a wide gap between front-end commission and average
     $/conversion (when the user supplied both) is the receipt that bumps /
     upsells / rebills exist. Whether affiliate attribution CARRIES into that
     backend is the decisive unknown — record backend.credit as
     verified|inferred|unknown, never assumed. extract_product_page on the
     vendor's funnel/order pages for visible bumps and tiers; get_domain_ads /
     search_facebook_ads on the VENDOR name for sibling products (upgrade,
     membership, pro, bundle).
   - The affiliate's OWN backend: map the buyer's journey — problem ->
     immediate solution -> implementation -> enhancement -> maintenance ->
     NEXT logical problem — and name complementary affiliate offers (other
     vendors welcome) for the later stages. Captured on a presell/list, the
     front-end offer is an acquisition vehicle for that chain, and the list is
     the asset that stops re-buying the same audience from the ad platform.
   Score backend.expansion_score 1-10 (count of complementary problems,
   credible adjacent affiliate offers, recurring revenue, repeat-purchase
   frequency, email potential, high-ticket escalation). Steps this tool cannot
   perform — walking the checkout, reading post-purchase emails, asking the
   affiliate manager whether rebills/upsells are commissioned and attribution
   persists — go in human_steps with the exact question to ask.
5. Score traffic-source fit. An offer converting on email or native can die on
   cold Meta — match the vendor's funnel type to the traffic temperature (cold
   paid needs a presell: advertorial / quiz / listicle from the catalog; the
   affiliate cannot edit the offer page, so the presell is the ONLY owned
   lever — name it by catalog slug). Weigh the vertical's platform-compliance
   burden: health/weight-loss/claim-heavy offers carry ban risk and restricted
   angles on Meta; physical non-supplement products carry a lower claim burden
   and are the safer first offer for an inexperienced buyer.
6. Return ONLY one JSON object in a ```json fenced block, no prose outside it,
   matching this schema (null/[] when unknown; NEVER invent numbers you did
   not retrieve or receive from the user):

```json
{
  "brief": {"marketplace": "", "niche": "", "traffic_source": "", "min_commission": null, "test_budget": null, "geo": ""},
  "market_read": {"summary": "", "popularity_trap_note": ""},
  "offers": [
    {
      "rank": 1, "name": "", "vendor": "", "niche": "", "funnel_type": "",
      "front_end_price": null, "commission": null, "average_payout": null,
      "payout_source": "user|page|unverified", "recurring": "",
      "ad_evidence": {"active_meta_ads": null, "distinct_advertisers": null, "longest_runtime": "", "google_payers": [], "signal": ""},
      "traffic_fit": {"score": 0, "temperature_match": "", "compliance_burden": "low|medium|high", "notes": ""},
      "economics": {"break_even_cpa": null, "epc_estimates": {"conservative": null, "base": null, "optimistic": null}, "assumed_cvr_range": "", "clicks_to_validate": null, "basis": "ESTIMATE"},
      "funnel_read": {"dominant_pattern": "", "presell_slug": "", "opportunity_gap": ""},
      "backend": {"fe_vs_avg_gap": "", "vendor_backend": [], "credit": "verified|inferred|unknown", "next_logical_problem": "", "complementary_offers": [], "expansion_score": 0},
      "opportunity_score": 0, "tier": "A|B|C", "risks": []
    }
  ],
  "winner": {
    "name": "", "why": "", "avatar": "", "angle": "", "creative_concept": "",
    "presell_slug": "", "list_asset": "", "backend_sequence": [],
    "daily_budget": null, "creatives_to_launch": 0,
    "kill_rule": "", "scale_rule": "", "biggest_risk": ""
  },
  "runner_up": {"name": "", "why_it_lost": ""},
  "human_steps": [
    {"step": "", "what_to_learn": ""}
  ],
  "validation_plan": [
    {"day": 1, "task": ""}
  ],
  "confidence_score": 0.0
}
```

Field notes: opportunity_score is 0-100, weighted roughly traffic-source fit
20%, payout economics 20%, ad-activity evidence 15%, vendor funnel quality
10%, market size 10%, creative potential 10%, competition 5%, presell
potential 5%, backend/recurring 5% — never bend the weighting to force a
predetermined winner — but rank by acquisition economics AND backend depth
together: when backend.expansion_score materially separates two offers, a
deeper ecosystem may outrank a modestly higher one-and-done payout, and the
winner's "why" must say so when it does. Tier A = receipts + economics + fit
all line up (test first); B = promising with one named uncertainty; C = watch
list. ad_evidence numbers come only from tool calls; payout figures only from
the user or an extracted page — otherwise null + "unverified".
ad_evidence.longest_runtime is a short phrase ("since 2026-06-16, ~10 weeks"),
not a sentence — it renders in a table column.
backend.fe_vs_avg_gap states the front-end-commission vs average-$/conversion
read in one sentence; backend.credit is verified only with a source, else
inferred/unknown; complementary_offers and winner.backend_sequence name the
next-logical-problem chain in purchase order (other vendors welcome);
winner.list_asset names the email-capturing presell asset that makes the list,
not the click, the thing being bought. human_steps carry the funnel-autopsy
work only a human can do (walk the checkout as a normal customer per network
rules, read post-purchase emails, ask the affiliate manager about attribution
carry-through and rebill commissions) with the exact question each step
answers. kill_rule and scale_rule are fixed BEFORE spend and stated as
concrete spend thresholds against the payout. validation_plan is ~5-7 days
from research to go/no-go. Keep every string to one concise sentence and
return complete, closed JSON — trim depth (fewer offers) before you sacrifice
validity."""
