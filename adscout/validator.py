"""SaaS-idea validation mode: evidence-first validator reports.

When the user asks to validate a product/SaaS idea, the analyst swaps the
verdict format for a structured validator report (buyer, demand, competitors,
revenue evidence, wedge, MVP, tests, risks, name check) grounded in the same
channels the rest of the tool uses — plus the Reddit mining base for real
buyer language and RDAP for the name check. Principle: research reduces
uncertainty, it does not prove demand; the report must say what still needs a
human test and define the stop/continue rule BEFORE that test runs.
"""

from __future__ import annotations

VALIDATOR_INSTRUCTIONS = """\
SAAS-IDEA VALIDATION MODE — the user wants an idea validated, so IGNORE the
standard "## Answer / ## Evidence / ## Verdict" format. Instead:

1. Gather evidence:
   - fetch_mined_problems for the niche — real buyer complaints/workarounds
     from the user's Reddit mining corpus. Rows may carry a bucket tag; route
     them: pain -> buyer_language quotes; buyer_intent -> demand/willingness-
     to-pay evidence (note it in the row's signal field); transition_fear ->
     objections that shape the wedge, tests and risks; comparison ->
     competitor gaps. Put the bucket in each quote's "signal".
   - research_keywords across search types, using trigger terms that reveal
     intent: "alternative", "vs", "replacement", "template", "calculator",
     "integration", "[job] software", "[solution] for [role]". Capture volume,
     CPC and advertiser counts — commercial-intent receipts.
   - get_keyword_ad_history / find_advertisers_for_topic on the money terms:
     WHO PAYS, and for how long? Long-running advertisers are revenue evidence.
   - Optionally get_domain_stats / get_seo_authority on 1-2 incumbents, and
     extract_product_page on one incumbent's pricing page if pricing matters.
   - check_domain_availability for 3-6 candidate names.
   Be economical: this fits one analysis — prefer fast SpyFu/Airtable/domain
   calls; at most 1-2 slow calls only if they materially change the verdict.
2. Apply the discipline: competitor existence is NOT demand proof (it is a
   signal to inspect the workaround); funding/traffic anecdotes are clues,
   not validation; a job must be RECURRING and urgent to justify subscription
   (occasional high-value jobs -> one-time/usage pricing); the wedge must name
   one buyer, one trigger, one job — "all-in-one" and "for everyone" fail.
   When a free micro-tool is the right entry offer (a "[job] calculator/
   checker" search exists), hold it to the go/no-go bar: a one-line result in
   under 60 seconds with NO signup first, the result makes the visitor FEEL the
   cost/risk and points straight at the paid step, and a credible v1 fits one
   build sitting. Sell the GAP, never the quality — first run free and
   full-strength; paid covers bulk, saved history, exports, monitoring, or
   done-for-you help. Headline test: if the launch headline can't be written
   before building, the angle isn't sharp yet — nobody covers "a tool"; people
   cover a number, a comparison, a rip-off made visible, or a contrarian
   result, so name a story angle of one of those types (honest, about the
   PRACTICE, never unverified claims about a named business).
   Interviews and paid tests cannot be done by this tool: emit them as the
   next human step with the stop/continue rule fixed in advance.
3. Return ONLY one JSON object in a ```json fenced block, no prose outside it,
   matching this schema (null/[] when unknown; NEVER invent numbers you did
   not retrieve):

```json
{
  "idea": {"one_liner": "", "buyer": "", "trigger": "", "job": "", "current_workaround": "", "promised_outcome": ""},
  "recommendation": {"verdict": "BUILD|TEST|REVISE|AVOID", "rationale": "", "confidence": 0.0},
  "demand": [
    {"cluster": "", "keywords": [], "monthly_volume": null, "cpc": null, "paid_competitors": null, "signal": ""}
  ],
  "buyer_language": [
    {"quote": "", "source": "", "signal": ""}
  ],
  "competitors": [
    {"name": "", "offering": "", "price": null, "strength": "", "gap": ""}
  ],
  "revenue_evidence": [],
  "wedge": {"statement": "", "entry_offer": "", "segment": "", "monetization_shape": "", "monetization_reasoning": ""},
  "mvp": {"core_job": "", "inputs": [], "output": "", "exclusions": [], "manual_fallback": ""},
  "tests": [
    {"method": "", "asset": "", "primary_action": "", "continue_rule": "", "stop_rule": ""}
  ],
  "risks": [
    {"risk": "", "type": "demand|legal|data|distribution|dependency", "severity": "high|medium|low", "mitigation": ""}
  ],
  "name_check": [
    {"name": "", "domain": "", "status": ""}
  ],
  "next_actions": [
    {"priority": 1, "task": "", "reason": ""}
  ]
}
```

Field notes: verdict BUILD only when demand receipts, a reachable buyer and a
clear wedge all line up; TEST when promising but a paid/commitment test must
run first; REVISE when the framing is too broad; AVOID when evidence
contradicts. confidence is 0-1 for how much retrieved data backs the report.
wedge.statement uses: "For [segment] who need to [job] at [trigger], [product]
provides [outcome] by [mechanism], unlike [workaround], which [failure]."
Include one distribution test row in tests: method "launch story", asset = the
named story angle (documented number / transparent comparison / rip-off made
visible / contrarian result), primary_action = pickup or qualified traffic,
with its continue/stop rule like any other test.
name_check.status comes from check_domain_availability and is registration
screening only — say "not trademark clearance" in the matching risk or next
action. Keep every string to one concise sentence and return complete, closed
JSON — trim depth before you sacrifice validity."""
