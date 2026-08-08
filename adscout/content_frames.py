"""Content-framework catalog: named, buildable blog and landing-page structures.

A compressed catalog (our own words) of 7 blog-post frameworks and 15
landing-page types distilled from the site-build-system template library,
plus the routing rules that map search intent, funnel stage and traffic
temperature to the right structure. Loaded alongside RESEARCH_INSTRUCTIONS
(so recommended_page / recommended_asset name real frameworks by slug, with
an outline a builder can execute) and alongside COPY_FRAME (so every ad
concept names the congruent landing page type it should land on).

Kept compact on purpose: it rides in the system prompt, so it carries slugs,
jobs, section orders and routing — not the full build documentation.
"""

CONTENT_FRAMES = """\
CONTENT-FRAMEWORK CATALOG — when you recommend a page or content asset (in the
research JSON's recommended_page / recommended_asset / framework fields, or when
naming the landing page for an ad concept), choose from THIS catalog by search
intent and funnel stage, and name the framework by its exact slug. Do not invent
page types outside this list.

BLOG FRAMEWORKS (7) — slug | job | sourced from | section order | matched opt-in
upgrade | pick when:
- quote_post | round up published expert quotes into one argument | quotes experts
  already made publicly (no outreach) | lede -> 3+ quote cards (name/title, quote,
  your 2-4 sentence analysis, links) -> "what they agree on" synthesis -> opt-in |
  upgrade: the quote collection + synthesis as a PDF | pick when goal is
  relationships or rankings and you have public quotes but no direct access;
  tagged experts share it.
- interview | one expert answers search-phrased questions | one ~40-min expert
  recording (yields text + video + audio) | lede -> expert card -> Q&A with each
  question as a searchable H2 -> pull quotes -> video + audio embeds -> opt-in |
  upgrade: transcript or the expert's toolkit | pick when goal is search rankings
  (question H2s) and one expert will give you 40 minutes.
- stat_roundup | compile linked statistics people cite | published research and
  data | lede -> stat cards (big number, statement, linked source, your analysis)
  -> infographic version -> opt-in | upgrade: the full dataset as a spreadsheet
  (highest opt-in rate of the seven) | pick when goal is backlinks or list growth
  and citable data exists.
- youtube_cutup | turn a popular how-to video into a step-by-step post that ranks |
  someone else's popular video (screenshot + credit + embed; add your own
  correction/addition) | lede -> numbered steps (H2 + screenshot + description) ->
  full video embed -> opt-in | upgrade: the step-by-step checklist | pick when goal
  is rankings on how-to terms with ~90 minutes and no other sources.
- embed_reactor | react to an existing embeddable asset | any popular embeddable
  video/deck/infographic (comes with its own demand) | lede -> embed -> your
  reaction/analysis -> repeat up to 3 embeds -> opt-in | upgrade: the companion
  guide | pick when you need the fastest publishable post; the reaction is the
  entire value.
- content_aggregator | curate the best existing articles with stated criteria |
  5-10 best links on the topic | lede + selection criteria -> curator's note ->
  numbered resource cards (summary + why it made the list) -> opt-in | upgrade:
  the complete list as a PDF | pick when goal is relationships (every featured
  author is an outreach reason) and genuinely good links exist.
- crowdsourced | many experts answer ONE specific question | 4-10 direct expert
  responses (two-week lead, ~30-40% reply rate) | lede -> the question, prominent
  -> respondent cards with full answers -> synthesis grouped by theme -> opt-in |
  upgrade: the response summary | pick when goal is backlinks + relationships and
  you have a network and two weeks.
Every blog framework ends with an end-of-post opt-in and pairs a MATCHED content
upgrade (never a generic newsletter box); the sourced material is the input, your
analysis/synthesis is the product.

LANDING PAGE TYPES (15) — slug | job | section order | primary conversion event |
traffic temperature fit:
- splash | one offer, zero exits, single CTA | hero only (eyebrow, outcome H1,
  mechanism subhead, single CTA, risk reducer) | affiliate_click | hot (your list,
  your buyers).
- squeeze | trade the click for the email | hero with form (benefit-first promise
  H1, 3-5 bullet specifics, name+email only, privacy line) | generate_lead | cold
  to warm traffic that needs more than one touch.
- full_funnel | opt in, immediate upsell, confirm | optin panel -> upsell panel
  (+ tracked skip) -> confirmation | generate_lead -> begin_checkout -> purchase |
  hot; requires a lead magnet AND something to sell right after.
- review | convert "[product] review" brand-name search | verdict box above the
  fold -> category scores -> pros/cons -> review body -> final CTA | affiliate_click
  | warm decision-stage search; real cons are mandatory.
- comparison | convert "best [category]" and "A vs B" | hero -> winner callout ->
  comparison table (winner highlighted) -> product cards | affiliate_click per
  merchant | warm comparison-stage search.
- steps | rank on how-to and bridge to the tool at the point of need | hero ->
  numbered steps with tools linked inline where needed -> final CTA (the toolkit)
  | affiliate_click | cool learning-intent search.
- arbitrage | maximise CTR on cheap traffic; no content; always noindex | hero
  (plain category question) -> 3-5 offer tiles -> aggregate CTA | affiliate_click
  per tile | cold display/native.
- arbitrage_interactive | qualify with two questions, then route to matched offers
  | hero -> step 1 question -> step 2 question -> 3 matched results |
  cta_click steps -> affiliate_click | cold display/native where the offer varies
  by input; two clicks of investment lift results CTR.
- advertorial | warm cold paid traffic: teach first, then bridge | hero (specific,
  dated, believable transformation) -> story (person/problem/attempt/discovery) ->
  soft mid CTA -> mechanism explained -> harder final CTA | affiliate_click (mid vs
  final) | coldest paid traffic; every claim must be substantiated.
- sales | sell direct, long form | hero (outcome + number + timeframe) -> problem
  agitation -> benefits/modules -> testimonials -> pricing + CTA -> FAQ ordered by
  objection frequency | purchase or affiliate_click | hot, problem-aware traffic.
- informational | rank a broad "N tips" query and recommend several tools | hero ->
  jump-link TOC -> tips as H2s with inline tool recommendations -> final CTA (the
  complete playbook) | affiliate_click | cool browsing-intent search.
- recommendation | own one "best [X] for [audience]" long-tail term with a
  first-person single answer | author credential block -> hero -> the flat
  recommendation + CTA -> why over everything else -> alternatives (each linked) |
  affiliate_click | warm narrow comparison search.
- download | the asset IS the offer; freshness is the lever | hero + "updated
  [month year]" badge -> download CTA -> what's inside -> social proof |
  file_download (if gated: generate_lead first) | warm clicks from your own content.
- resource | evergreen "what do you use for X" hub everything links to | hero ->
  featured #1 pick -> category sections, 2-4 tools each (cap at four) |
  affiliate_click per category | warm-to-hot trusting audience.
- slide | pace an argument for mobile / low-patience visitors, one claim per slide
  | slide 1 problem -> 2 reframe/mechanism -> 3 proof -> 4 offer -> 5 CTA (never
  more than ~6) | cta_click per slide -> affiliate_click | cold-to-cool mobile
  social traffic.

ROUTING — map intent to page type:
- "[product] review" -> review; "best X" / "X vs Y" -> comparison; "best X for
  [audience]" -> recommendation; "how to X" -> steps (or a youtube_cutup blog
  post); "N tips" -> informational; "[category] statistics" -> stat_roundup blog.
- Cold paid click -> advertorial (skeptical, needs the story) or arbitrage /
  arbitrage_interactive (cheap display/native, just route them); warm list/email
  click -> splash or sales; click from your own content -> squeeze or download;
  "what do you use for X" -> resource; mobile social -> slide.
- Temperature rule: the colder the traffic, the more the page must teach before
  the ask (an advertorial earns the offer over ~800 words; a splash skips straight
  to it). Cold->hot ladder: advertorial/arbitrage -> informational/steps/squeeze ->
  review/comparison/recommendation/resource -> splash/sales/full_funnel/download.
- Never: a squeeze page on brand-name search (wastes a ready buyer); long-form
  sales on cold display; arbitrage pages indexed; a comparison page with one
  product (that's a review — call it one).

BLOG -> LANDING PAIRING — the post is the top of the funnel; pair it with the page
matching what the reader was just persuaded of (blog slug -> landing slug(s),
bridge asset):
- stat_roundup -> squeeze or download; bridge: the full dataset.
- youtube_cutup -> steps or download; bridge: the step-by-step checklist.
- interview -> recommendation or squeeze; bridge: the expert's recommended tool.
- quote_post -> informational or resource; bridge: the tools they all mentioned.
- embed_reactor -> review or comparison; bridge: deeper analysis of the asset
  reacted to.
- content_aggregator -> resource; bridge: the curated list, expanded.
- crowdsourced -> squeeze or comparison; bridge: the response summary."""
