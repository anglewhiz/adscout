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
