"""Affiliate bridge-campaign spec mode: data-defined strategy, prompts to build.

When the user asks for a bridge campaign (Funnelology's Bridge Funnel & Offer
Differentiation Framework), the analyst emits a machine-readable campaign spec
instead of prose: the strategy grounded in ad-library/SEO receipts, plus one
ready-to-paste generation prompt per asset, each tagged with the downstream
tool that builds it. Principle: most affiliates send traffic straight to the
vendor's page and compete on nothing — the ownable assets are the presell, the
list, and the OFFER WRAPPER (bonuses that solve the buyer's post-purchase
follow-up problems), launched in sync with the vendor's own marketing wave,
which the ad libraries make visible.
"""

from __future__ import annotations

BRIDGE_INSTRUCTIONS = """\
BRIDGE-CAMPAIGN SPEC MODE — the user wants a complete Affiliate Bridge
Campaign defined by data and handed downstream as buildable prompts. IGNORE
the standard ## Answer / ## Evidence / ## Verdict format. Work through the
framework below, then return ONE JSON object.

THE FRAMEWORK (Bridge Funnel & Offer Differentiation). Affiliates competing on
the same product own only three things: the presell, the list, and the offer
wrapper. So: (1) wrap the core product in a differentiated offer — bonuses
that solve the FOLLOW-UP problems the buyer hits after purchase, at least one
per belief category: VEHICLE ("does the product work?" — quick-start guides,
walkthroughs), INTERNAL ("can I make it work?" — step-by-step plans,
over-the-shoulder demos), EXTERNAL ("do I have the time/tools/money?" —
templates, done-for-you assets, resource lists). (2) Pre-frame the sale with a
bridge page and a Day 0-4+ belief-journey sequence: Day 0 origin story, Day 1
vehicle proof, Day 2 internal ("people like you succeeded"), Day 3 external
(resources solved — spotlight the external bonuses), Day 4+ pitch + bonus
stack + deadline. (3) Launch in sync with the vendor's own marketing wave —
promote what they promote, when they promote it. The message chain is: the
HOOK sells the sales message, the SALES MESSAGE sells the offer — a weak link
anywhere breaks the funnel.

HOW TO WORK:
1. Ground the campaign in an offer. If this thread already contains an offer
   report or a named offer, build on it and DO NOT re-research what the
   thread already established. Otherwise the user must have named a product —
   verify it with at most TWO slow calls total (this mode is synthesis-heavy:
   prefer zero new slow calls when thread evidence exists).
2. Run the product vet WITH RECEIPTS where the tools can reach: notable_brand
   from SEO authority + branded search presence; vendor_markets_itself from
   live Meta/Google ad activity (fresh creative starts = an active wave);
   recurring/upsells from the thread's backend read or extracted pages, else
   "unknown". user_belief is ALWAYS a human field — never invent the user's
   experience with the product. A failed criterion never blocks the campaign;
   record the adaptation it forces (no recurring -> bonuses must drive
   front-end conversion; weak brand -> heavier proof burden on the bridge
   page).
3. Time the launch. Read the vendor's CURRENT ad wave (new creatives, fresh
   start dates, angle iterations) and make a concrete timing call — ride the
   live wave now, or wait for the next push. Cite the receipt.
4. Mine observed ad angles (from this thread or fresh lookups) for the hook
   and story: the angles already spending money are the belief-shift language
   the market responds to. hook_url_ideas are 5-8 short, spellable,
   curiosity-sparking domain ideas — availability UNCHECKED (that is a human
   step).
5. Write the origin story as BEATS (Hook -> backstory -> wall -> discovery ->
   result -> why I promote it -> bonus walkthrough -> exact buy steps), with
   placeholders where the user's real story must fill in — NEVER fabricate
   personal experience, results, or testimonials. The social_proof_plan maps
   each available proof piece to the belief it supports and names what is
   missing plus an ethical way to get it.
6. Emit the ASSETS — the heart of the spec. One entry per buildable artifact,
   each with a self-contained `prompt` a downstream tool can execute without
   this conversation's context (embed the avatar, angle, offer, bonuses, and
   compliance constraints INSIDE the prompt text). Tag each with `handoff`:
   - "bridge_skill"   — the user's affiliate-bridge-campaign Claude skill
                        (full campaign folder: brief, bonus stack, messaging,
                        page copy, emails, checklist)
   - "page_builder"   — WordPress/Claude landing-page builder (bridge page,
                        advertorial, quiz)
   - "creative_tool"  — image/video ad generator (per-angle ad creatives)
   - "aweber"         — email platform (list, welcome + belief-journey
                        sequence)
   - "airtable"       — campaign tracker (the spreadsheet row spec)
   - "make"           — automation scenarios (organic distribution posts)
   - "meta_ads_manager" — campaign/adset/ad structure + budgets + rules
   Include ONE "bridge_skill" asset whose prompt serializes the campaign as
   that skill's intake (product, niche & audience, story angle + placeholders,
   proof inventory, traffic source, vendor launch calendar).
7. Emails: one entry per day (0 through 4+), each with the belief it kills, a
   subject direction, and a complete self-contained generation prompt.
8. Tracking: affiliate-link placement rules (bridge page CTA + email CTAs),
   UTM template, and the conversion events worth wiring.
9. Anything the tools cannot know goes in human_steps (user's story, proof
   collection, hook-domain availability, affiliate-network approval, bonus
   delivery mechanics) and assumptions — labeled, never silently invented.

Return ONLY one JSON object in a ```json fenced block, no prose outside it,
shaped exactly like this:

```json
{
  "campaign": {
    "name": "", "objective": "",
    "offer": {"product": "", "vendor": "", "network": "", "payout": null, "payout_source": "user|extracted|unverified"},
    "niche": "", "avatar": "", "traffic_source": "", "geo": ""
  },
  "product_vet": {
    "notable_brand": {"score": 0, "evidence": ""},
    "recurring_commissions": {"status": "yes|no|unknown", "evidence": ""},
    "upsells": {"status": "yes|no|unknown", "evidence": ""},
    "vendor_markets_itself": {"score": 0, "evidence": ""},
    "user_belief": "human step — never scored by the tool",
    "adaptations": ""
  },
  "differentiated_offer": {
    "core_product": "",
    "bonuses": [
      {"name": "", "belief": "vehicle|internal|external", "follow_up_problem": "", "format": "", "stated_value": ""}
    ]
  },
  "messaging": {
    "hook_url_ideas": [],
    "observed_angles": [{"angle": "", "source": ""}],
    "origin_story_beats": [],
    "social_proof_plan": [{"proof": "", "belief": "", "status": "have|missing", "how_to_get": ""}]
  },
  "launch_sync": {"vendor_wave_evidence": "", "timing_call": ""},
  "assets": [
    {"id": "", "type": "", "handoff": "bridge_skill|page_builder|creative_tool|aweber|airtable|make|meta_ads_manager", "title": "", "depends_on": [], "prompt": "", "notes": ""}
  ],
  "email_sequence": [
    {"day": 0, "belief": "", "subject_direction": "", "prompt": ""}
  ],
  "tracking": {"utm_template": "", "link_placement_rules": [], "conversion_events": []},
  "human_steps": [{"step": "", "what_to_learn": ""}],
  "assumptions": [],
  "confidence_score": 0.0
}
```

FIELD NOTES. Asset prompts are the deliverable: each must stand alone — a
person pasting one into a fresh session with no other context should get the
right artifact, so restate the avatar, angle, offer economics, bonus stack,
and the platform-compliance constraints (no fabricated endorsements, no
prohibited health/earnings claims, no fake scarcity) inside every prompt.
Asset ids are kebab-case and depends_on references them (creatives depend on
the angle assets; emails depend on the bonus stack). email_sequence prompts
follow the same self-containment rule. The bonus stack must cover all three
beliefs or say which is uncovered and why. product_vet evidence names its
source (thread report, tool call, or "unverified"). hook_url_ideas carry no
availability claim. launch_sync.timing_call is one concrete sentence ("launch
within N days while the wave runs" / "wait for the next push, watch X").
Every factual claim keeps the VERIFIED/SIGNAL/ESTIMATE discipline of the
system prompt; the user's story, proof, and belief stay human placeholders.
Keep strings tight and return complete, closed JSON — drop optional assets
before you sacrifice validity."""
