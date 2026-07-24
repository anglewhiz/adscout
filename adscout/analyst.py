"""The analyst: turns a marketing question into SpyFu calls and a grounded answer.

Uses Claude's tool-use loop. Claude reads the question, decides which SpyFu
tools to call, we execute them, feed results back, and Claude synthesizes a
verdict that cites concrete numbers. Every tool call is recorded in a trace so
the reasoning is auditable.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

import re

from .client import SpyFuClient
from .copywriting import COPY_FRAME
from .research import RESEARCH_INSTRUCTIONS, extract_research
from .strategy import STRATEGY_FRAME
from .tools import TOOLS, dispatch

SYSTEM_PROMPT = """You are a paid-search and SEO marketing analyst. You answer \
marketing questions using competitive-intelligence data across two channels, and \
your job is to PROVE or DISPROVE the user's idea with evidence — never to guess.

You have THREE data channels — use whichever the question needs, and don't \
conclude from just one:
- GOOGLE SEARCH ads (SpyFu): find_advertisers_for_topic, research_keywords, \
get_keyword_ad_history, get_domain_ads, get_top_ppc_competitors, get_domain_stats.
- FACEBOOK/INSTAGRAM ads (Meta Ad Library): search_facebook_ads, \
get_advertiser_facebook_ads — live ad creatives, offers, and CTAs.
- ORGANIC SEO AUTHORITY (Moz): get_seo_authority (Domain Authority, spam score, \
linking root domains), get_linking_domains (who links to them), get_top_pages \
(which pages earn the links).
- VISUAL: capture_landing_page screenshots a destination page (mobile+desktop) \
and shows it to the user. Great for the landing page behind a Meta ad (its \
linkUrl) or a funnel/offer page. Slow and metered — at most 1-2 per answer, only \
when seeing the page matters. The image is displayed automatically; never paste \
the image URL into your answer.
- CREATE: generate_creative makes NEW ad creatives or landing-page hero mockups \
as images. Only when the user asks to design/create/mock up something for THEIR \
offer — never to research competitors. Ground the brief in the hooks, offers and \
angles you actually found, and say in one line why the concept follows from the \
evidence. Metered: at most 2 calls per answer.

Rules:
- Ground every substantive claim in data you retrieved via the tools. If you did \
not pull a number, do not assert it.
- Plan briefly, then call tools. Typical niche flow: find who advertises on Google \
(find_advertisers_for_topic), inspect ad copy (get_keyword_ad_history), size up \
advertisers (get_domain_stats).
- IMPORTANT: if Google Search shows little or NO paid activity, that does NOT mean \
the offer isn't advertised — many offers (especially $1-trial/continuity funnels, \
info-products, coaching, DTC) run mainly on Meta. In that case ALWAYS check \
search_facebook_ads (by topic) and get_advertiser_facebook_ads (by the brand/Page) \
before concluding. Only call a niche 'not advertised' if BOTH channels are empty.
- Use Moz to judge whether a brand is an established operator (Domain Authority, \
linking domains) vs thin//new, and to size up how hard a niche is to rank in. A \
site with no ads but strong authority competes organically, not on spend.
- Note data limitations honestly (estimates, sample sizes, single-country scope, \
and which channel a finding came from).

FORMAT — return the final answer as Markdown in exactly this shape:

## Answer
Two to four sentences answering the question directly, up front.

## Evidence
A "### " sub-heading for EACH channel you actually pulled data from — use the \
names "Google Search (SpyFu)", "Facebook & Instagram (Meta)", "SEO Authority \
(Moz)". Under each, tight bullets of concrete findings with the **numbers in \
bold**. Omit any channel you did not use. If a channel returned nothing, say so \
in one bullet — that absence is itself evidence.

## Verdict: SUPPORTED
(Use SUPPORTED, REFUTED, MIXED, or INCONCLUSIVE on that heading line.) Follow \
with one sentence of reasoning, then:

**Key numbers**
- 3-6 bullets, each a concrete figure with its channel in parentheses.

Style: bold every metric, keep bullets to one line where possible, no filler or \
restating the question. Never invent a number to fill the template.

When a "## Strategic read" applies (see the lenses below), place it after the \
Verdict block as the closing section.

""" + STRATEGY_FRAME

# Verbs and objects that signal the user wants a creative MADE (not researched).
# When both appear, the ad-copy playbook is added to the system prompt for that
# run; otherwise it's omitted to keep ordinary analyses lean.
_CREATE_VERBS = ("creat", "design", "mock up", "mockup", "generate", "make me",
                 "give me", "come up with", "write", "draft", "produce")
_CREATE_NOUNS = ("ad ", "ads", "advert", "creative", "concept", "copy",
                 "headline", "landing page", "banner", "mock-up", "mockup")


_EMPTY_FALLBACK = ("The analysis ran but didn't produce a written summary — this "
                   "can happen on complex requests. Try again, narrow the question, "
                   "or raise Max steps. The evidence trace below shows what was gathered.")


def _wants_creative(question: str) -> bool:
    q = question.lower()
    return (any(v in q for v in _CREATE_VERBS)
            and any(n in q for n in _CREATE_NOUNS))


def _wants_keyword_research(question: str) -> bool:
    """Detect a request for a structured keyword/niche research object."""
    q = question.lower()
    if any(t in q for t in ("research object", "as json", "json object")):
        return True
    if "keyword" in q and any(w in q for w in (
            "research", "find", "opportunit", "niche", "underbelly", "cluster",
            "best ", "list of")):
        return True
    return False


@dataclass
class ToolCall:
    name: str
    input: dict
    result_summary: str


@dataclass
class AnalystResult:
    answer: str
    trace: list[ToolCall] = field(default_factory=list)
    steps: int = 0
    # Landing-page captures made during the run, rendered as a gallery.
    screenshots: list[dict] = field(default_factory=list)
    # Images generated during the run (ad concepts / hero mockups).
    creatives: list[dict] = field(default_factory=list)
    # Structured keyword-research object (keyword-research mode only).
    research: dict | None = None


class Analyst:
    def __init__(
        self,
        spyfu: SpyFuClient,
        *,
        anthropic_client=None,
        meta=None,
        moz=None,
        shots=None,
        creative=None,
        model: str = "claude-sonnet-5",
        default_country: str = "US",
        max_steps: int = 8,
        max_tokens: int = 2048,
    ) -> None:
        self.spyfu = spyfu
        self.meta = meta
        self.moz = moz
        self.shots = shots
        self.creative = creative
        self.model = model
        self.default_country = default_country
        self.max_steps = max_steps
        self.max_tokens = max_tokens
        if anthropic_client is None:
            import anthropic  # imported lazily so --mock/offline tests need no key
            anthropic_client = anthropic.Anthropic()
        self.ai = anthropic_client

    def ask(self, question: str) -> AnalystResult:
        messages = [{"role": "user", "content": question}]
        trace: list[ToolCall] = []
        screenshots: list[dict] = []
        creatives: list[dict] = []
        nudged = False

        # Pick the output mode from the question. Keyword-research swaps the
        # verdict format for a structured JSON object; creative adds the copy
        # playbook. Both are conditional so ordinary queries stay lean.
        research_mode = _wants_keyword_research(question)
        max_tokens = self.max_tokens
        if research_mode:
            system = SYSTEM_PROMPT + "\n\n" + RESEARCH_INSTRUCTIONS
            max_tokens = max(self.max_tokens, 4096)  # the object is large
        elif _wants_creative(question):
            system = SYSTEM_PROMPT + "\n\n" + COPY_FRAME
        else:
            system = SYSTEM_PROMPT

        for step in range(1, self.max_steps + 1):
            resp = self.ai.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                tools=TOOLS,
                messages=messages,
            )

            if resp.stop_reason != "tool_use":
                answer = "".join(
                    getattr(b, "text", "") for b in resp.content
                    if getattr(b, "type", None) == "text"
                ).strip()
                # The model occasionally ends its turn without writing anything.
                # Nudge it once to produce the written analysis rather than
                # returning a blank answer.
                if not answer and not nudged and resp.content and step < self.max_steps:
                    nudged = True
                    messages.append({"role": "assistant", "content": resp.content})
                    messages.append({"role": "user", "content":
                        "Now write your final analysis for the user in the required "
                        "Markdown format (## Answer, ## Evidence, ## Verdict, and the "
                        "creative sections if asked). Use the tool results already "
                        "gathered above."})
                    continue
                research = extract_research(answer) if research_mode else None
                return AnalystResult(
                    answer=answer or _EMPTY_FALLBACK, trace=trace, steps=step,
                    screenshots=screenshots, creatives=creatives, research=research)

            # Record the assistant turn (with its tool_use blocks) verbatim.
            messages.append({"role": "assistant", "content": resp.content})

            tool_results = []
            for block in resp.content:
                if getattr(block, "type", None) != "tool_use":
                    continue
                try:
                    data = dispatch(
                        self.spyfu, block.name, dict(block.input),
                        default_country=self.default_country, meta=self.meta,
                        moz=self.moz, shots=self.shots, creative=self.creative,
                    )
                    if isinstance(data, dict) and data.get("_generated_creative"):
                        creatives.append({
                            "label": data.get("label"),
                            "format": data.get("format"),
                            "brief": data.get("brief"),
                            "images": data.get("images") or [],
                        })
                    if isinstance(data, dict) and data.get("_captured_screenshot"):
                        screenshots.append({
                            "label": data.get("label"),
                            "source": data.get("source"),
                            "images": data.get("images") or {},
                        })
                    payload = json.dumps(data)[:6000]  # bound token growth
                    trace.append(ToolCall(block.name, dict(block.input),
                                          _summarize(data)))
                except Exception as exc:  # surface errors to the model, keep going
                    payload = json.dumps({"error": str(exc)})
                    trace.append(ToolCall(block.name, dict(block.input), f"error: {exc}"))
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": payload,
                })

            messages.append({"role": "user", "content": tool_results})

        return AnalystResult(
            answer="Stopped after reaching the maximum number of analysis steps. "
                   "Partial evidence is in the trace above.",
            trace=trace,
            steps=self.max_steps,
            screenshots=screenshots,
            creatives=creatives,
        )


def _summarize(data: dict) -> str:
    results = data.get("results")
    if isinstance(results, list):
        total = data.get("totalMatchingResults")
        tail = f" of ~{total} total" if total else ""
        return f"{len(results)} rows{tail}"
    return "ok"
