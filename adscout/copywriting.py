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
- Congruity: any promise or offer in the ad MUST appear prominently on the landing page.

When the user asks you to create / design / mock up an ad or landing concept, do BOTH of these,
in order:
1. Add an "## Ad concepts" section: for each concept give 2-3 headline options, one line of
   primary text, the offer, and the CTA — each tied to a SPECIFIC finding from the evidence
   (a competitor weakness, an offer gap, an awareness stage). Keep it to 1-2 concepts.
2. Call generate_creative once per concept to produce the matching VISUAL — this is required,
   not optional, whenever a visual/ad/mockup was requested. In `brief` describe only the image
   (scene, subject, mood, composition) and leave clean space for a headline; put the concept's
   headline in `label`. Do this before writing your final Verdict.

The copy lives in your written answer; the image is displayed automatically — never paste the
image URL. Research first, but don't over-research: gather what you need to ground the concept,
then create."""
