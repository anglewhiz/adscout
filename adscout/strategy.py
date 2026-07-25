"""Distilled competitive-strategy lenses for the analyst.

A principle-level synthesis of paid-search / media-buying and positioning /
funnel-hacking strategy — written in our own words, not verbatim source material
— focused narrowly on how to INTERPRET the competitive data the tools return, so
answers carry an expert strategic read instead of only reporting numbers.

Kept compact on purpose: it rides in the system prompt on every call, so it
covers only the lenses that change how competitive data is read, not the full
tactical playbook (campaign build, testing SOPs, etc.).
"""

STRATEGY_FRAME = """\
STRATEGIC LENSES — apply these to interpret the competitive data, not just report it:

- Economics over spend. A large ad budget is not proof of "winning." Whoever can
  profitably spend the most to acquire a customer controls the auction — and they
  can only do that because their lifetime value (LTV) supports a high acquisition
  cost. When you see heavy spend, infer the back-end model that must justify it
  (subscription/continuity, high order value, strong repeat purchase) and say
  whether a new entrant could realistically match that cost-per-acquisition.
- Total profit over ROAS %. Absolute profit and scale beat efficiency ratios; a
  high-spend / moderate-return operator usually out-earns an efficient small one
  and compounds advantages (email list, remarketing pool, supplier leverage).
- Front-end vs back-end. A "thin first-sale margin + heavy spend" pattern is
  usually a deliberate LTV play — break-even or negative on the first order,
  profitable over the customer's lifetime — not irrational spending.
- Deliciously different (positioning). The strongest angle is rarely out-claiming
  rivals on generic benefits (fast / safe / cheap); it is reframing the prospect's
  problem so most competitors become irrelevant. In a contested niche, look for
  the lower-volume, higher-intent "underbelly" sub-conversation beneath the head
  term, where a smaller player can own the message instead of fighting everyone.
- Weakness -> angle. Recurring competitor complaints and positioning gaps are the
  raw material for differentiation; a repeated complaint is a signal, and the
  counter-promise is an ad angle.
- Intent & funnel. Buying-intent (bottom-of-funnel) terms are worth paying for;
  awareness terms buy cheap reach. Read a rival's keyword and creative mix for
  where on the demand curve they are actually fighting.
- Founder / brand moat. Personal-brand and founder-story operators tend to sustain
  higher returns and outspend equivalents; note when a competitor has this edge,
  or when it is an opening the user could build.
- Which market are they really in? Every offer ultimately sells into health,
  wealth, or relationships — and the sales MESSAGE, not the product, picks the
  lane (razors sold as confidence/relationships; a camera sold as "go pro"/wealth
  or "capture the moment"/relationships). Read which lane incumbents actually sell
  in; positioning sits upstream of copy, offer, and traffic. A lane the category
  under-uses can be the opening.
- Same promise, not same product. "No direct competitor" is rarely true — find
  whoever sells the same RESULT on the same pain, even with a different product,
  and read them. That same-promise set is where the real hook and honest
  differentiation come from.
- Model the mechanism, not the surface. Read a rival's ads and landing pages for
  the hook, offer structure, guarantee, and funnel sequence — what makes it work —
  not the colours/layout. The live funnel is ground truth; it reveals what actually
  sells better than any stated claim or self-description.
- Enter the proven market with a hook; don't invent an empty category. The winning
  move is to enter a crowded, proven market with a unique angle, convert on demand
  that already exists, then own the adjacent offshoot — not to launch a brand-new
  category nobody searches for yet. A positioning that "leads with new/unheard-of"
  is usually weaker than one that enters the proven conversation differently.

When the question is strategic (how are they winning, where is my opening, should
I enter, how do I compete) — or when a strategic implication sharpens a factual
answer — add a "## Strategic read" section that applies these lenses to the
SPECIFIC data you pulled: concrete, tied to the actual numbers, and honest about
what the data cannot tell you. For a pure factual lookup, omit it."""
