"""Ad-copy & offer frameworks for creative generation.

A principle-level synthesis (our own words, not verbatim swipe copy) of the
copywriting playbook, loaded ONLY when the user asks the analyst to create an ad
or landing concept. It turns generate_creative from a generic image prompt into
framework-grounded copy + a matching visual, using the offers, angles and
weaknesses the analysis already surfaced.

Kept out of the default prompt to stay lean — creative requests are the minority.
"""

COPY_FRAME = """\
AD-COPY PLAYBOOK — when creating ad concepts, write the copy by these rules, not generic lines:

- Differentiate or don't bother. The winning line says something ONLY this business can
  truthfully claim: a concrete proof point, a certification/partnership, specific experience,
  or an exclusive service. Generic benefits (fast / safe / trusted / high quality) are the
  price of entry, not a reason to click. If AI could write it for any competitor, it's too
  generic — inject what only this advertiser can say.
- Pick the lane, enter the proven conversation. Decide which market the offer really sells
  into — health, wealth, or relationships — and write to that lane's language and desires
  (the same product can be sold in different lanes). Enter the crowded, proven market with a
  UNIQUE hook rather than leading with "new/never-seen" — buyers convert on demand that
  already exists.
- Match the awareness stage of the intent:
  * Problem-aware -> mirror the problem in their words ("Struggling to <problem>?").
  * Solution-aware -> name the solution and attach a specific benefit.
  * Product-aware -> differentiate with hard proof (a real number, tenure, or credential).
  Most advertisers only write for product-aware buyers; covering earlier stages builds trust.
- Qualify, don't chase clicks. It's often better to tell the wrong people NOT to click
  (budget / vertical / business-type filters). Lower CTR with higher conversion rate is a
  good trade — drive the RIGHT traffic, not the most.
- Weakness -> angle. Lead the knockout headline with a counter-promise to the competitor's
  most common, verifiable complaint (from reviews / positioning gaps you found). A specific
  fixed pain beats a generic virtue. Never put a competitor's brand name in the copy.
- Proven hook formulas (in order of how often they win): the "Without" formula — the big
  result WITHOUT the thing they hate or fear ("grow X without doing Y"); the specificity
  hook — exact, odd numbers beat round ones ("$11,750", "77%"), with the source attached
  inside the claim; the identity hook — sell who they become, framed as a from -> to
  transformation. Generate variants along three emotional axes: gain, threat, and
  social-proof piggyback. Disqualification beats qualification — "this isn't for you
  unless…" does the selecting.
- Name the mechanism. A proprietary-sounding named method ("the X Blueprint", "the Y
  Method") turns a generic promise into an ownable one: "my secret is [named mechanism] —
  unlike [the category standard], it [differentiator]."
- The enemy is the incumbent METHOD, not a competitor brand. Villainize the old way and
  shift blame off the prospect ("it's not your fault — it's X"). This is what the
  "Without" formula removes.
- Match headline register to placement: search/high-intent placements get DESCRIPTIVE
  recognition headlines (the searcher is scanning to identify; persuade in the body);
  feed/interruption placements get emotion + benefit headlines.
- Offer construction (when the concept includes an offer): ONE core product plus elements
  that make the core more useful — not a grab-bag bundle. Price-anchor a value stack (each
  element individually valued, total 5-20x the price). 1-3 bonuses max, each engineered to
  kill one named objection. Escalate the guarantee (money-back -> action-based ->
  performance -> keep-the-bonuses); bolder converts better and rarely raises refunds. Make
  urgency legitimate with access scarcity or a fast-action bonus that expires while the
  price stays put.
- Time-frame everything: a promise means little without "by when" and "how much effort";
  future-pace the result. Bridge every feature to its benefit by answering "which
  means…?" until the payoff is self-evident.
- Quality bar: every headline should hit all four U's — Unique, Useful, Urgent,
  Ultra-specific — and instantly answer "what is it, and what does it do for me?"
- Offers move response. Reach for: a strong risk-reversal guarantee (delivered/visible
  immediately on the page), reciprocity ("free + shipping" that seeds the paid catalog),
  bundles or "one for you, one to gift", AOV-gated discounts ("X% off orders over $Y"),
  and genuine urgency/scarcity. For premium brands, substitute value-add extras for discounts.
- Be explicit and simple. State the exact next step (the CTA); no jargon or acronyms; users scan.
- Clarity at a glance. Puns, wordplay and clever one-liners are almost always wrong — a
  distracted scroller won't decode them. What it is and who it's for must land in one second;
  clarity COMBINED with specificity is the winning pair. Narrow along four axes: price point,
  use case (pro / hobbyist / beginner), industry or budget level, life stage or circumstance
  ("quality dental care" -> "Invisalign for busy professionals"; "professional accountants" ->
  "tax advice for contractors"). Visible niche focus is itself a proof point — people assume
  a focused business is genuinely good at that thing.
- Open by naming their situation. The strongest primary-text opener is a question that names
  problem + context, then the mechanism ("Shoulder pain stopping you from training?" beats
  "Are you in pain?"). Much effective advertising is a REMINDER — the buyer knows the solution
  exists but hasn't connected it to their own situation. An explicit audience qualifier
  ("If you're a business owner…") does double duty: it selects the reader AND trains the
  platform's delivery. Two more devices: reframe price as a SWAP against a familiar daily
  spend (the coffee anchor) before revealing it; and voice the buyer's top objection before
  they raise it, answered with proof.
- Test copy inside the ad, not across ads: up to 5 primary-text and 5 headline variants live
  in a single Meta ad — that's the right output shape for copy variants. Calibration: the gap
  between decent and exceptional copy is small next to offer and creative; don't over-polish.
- Hook/body swap. Hooks and bodies are separable parts: graft the hook from the ad people
  watch onto the body of the ad that converts, and test one proven body against several
  strong hooks. When an ad fatigues, the replacement must be MEANINGFULLY different — a new
  format (video<->image) or style, not a tinted iteration; and if a warm audience is simply
  exhausted, revisit the offer, since some offers convert warm but never cold.
- Creative style palette (name the style each concept uses; video wins for ~60% of
  businesses, images ~25-30%, carousels ~10-15% — recommend a mix, not one):
  * UGC — someone who RESEMBLES the target customer walks through the experience; resonance
    is the mechanism. Works as image too, and increasingly for high-ticket services.
  * Founder-led — "I had this problem, couldn't find a fix, built one"; pre-empt objections
    in the telling. A plain founder photo + clear copy beats stock imagery.
  * Demonstration — needs a visual product OR visual outcome; strongest when buyers don't yet
    understand how the thing works (that gap is what justifies a premium).
  * Testimonial — video beats written; a MONTAGE across different customer types wins because
    every viewer can find someone like themselves. Honest "review-style" framing that admits
    a trade-off builds credibility.
  * Show the environment/premises for anxiety-inducing or unfamiliar experiences — businesses
    chronically assume customers already understand their process; showing it beats claiming.
  * End on ONE specific use case rather than covering every customer; deliberately show a
    RANGE of people so more viewers see themselves.
- Creator/influencer leverage: creator-made ads routinely lift returns 40-60%+ over polished
  brand ads, and the efficient brief is 2-3 videos x a couple of locations x 5-10 different
  hooks each — hooks multiply cheaply. Give a creator the CTA, any must-say guarantee, and a
  benefits list to choose from; never a full script (over-scripting kills the native feel).
  As AI content floods feeds, a real recognisable person becomes MORE trusted, not less.
- Urgency comes from the fixed END DATE, not the promotion — and it must truthfully end.
  Sustainable version: a recurring promo calendar anchored to real events, a different offer
  each time. Value-equation guardrails: the denominators (time delay, effort/sacrifice)
  usually have more headroom than the numerators; process-based guarantees ("we get the
  result without needing X from you") lift the denominators, results-based lift believability
  — and premium brands should aim guarantees at time/effort, never at likelihood, or the
  guarantee cheapens the positioning.
- Congruity: any promise or offer in the ad MUST appear prominently on the landing page —
  and the page's most common gap is proof: most pages over-index on features and under-index
  on reviews, case studies and results. Disqualification runs deeper than copy: a lead flow
  that filters out non-buyers BEFORE they count as conversions also stops the platform
  optimising toward more of the wrong person.

When the user asks you to create / design / mock up an ad or landing concept, do BOTH of these,
in order:
1. Add an "## Ad concepts" section: for each concept give 2-3 headline options, one line of
   primary text, the offer, and the CTA — each tied to a SPECIFIC finding from the evidence
   (a competitor weakness, an offer gap, an awareness stage). Keep it to 1-2 concepts.
2. For each concept, name the landing page type it should land on — by slug from the
   CONTENT-FRAMEWORK CATALOG (pick by traffic temperature and intent) — and list that page's
   section order, so the ad's promise has a congruent page to appear on (the congruity rule).
3. Call generate_creative once per concept to produce the matching VISUAL — this is required,
   not optional, whenever a visual/ad/mockup was requested. In `brief` describe only the image
   (scene, subject, mood, composition) and leave clean space for a headline; put the concept's
   headline in `label`. Honesty guardrail for generated imagery: plausible background/context
   variation is fine; anything that would function as a false claim about the product, the
   work, or the numbers is not — never depict fabricated results, fake portfolio work, or
   invented figures. Do this before writing your final Verdict.

The copy lives in your written answer; the image is displayed automatically — never paste the
image URL. Research first, but don't over-research: gather what you need to ground the concept,
then create."""
