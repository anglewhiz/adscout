"""The analyst: turns a marketing question into SpyFu calls and a grounded answer.

Uses Claude's tool-use loop. Claude reads the question, decides which SpyFu
tools to call, we execute them, feed results back, and Claude synthesizes a
verdict that cites concrete numbers. Every tool call is recorded in a trace so
the reasoning is auditable.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from .client import SpyFuClient
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
- End with a short, clearly labeled verdict: SUPPORTED / REFUTED / MIXED / \
INCONCLUSIVE, followed by the 3-6 facts (with channel) that drove it.
Keep the final answer tight and skimmable."""


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


class Analyst:
    def __init__(
        self,
        spyfu: SpyFuClient,
        *,
        anthropic_client=None,
        meta=None,
        moz=None,
        model: str = "claude-sonnet-5",
        default_country: str = "US",
        max_steps: int = 8,
        max_tokens: int = 2048,
    ) -> None:
        self.spyfu = spyfu
        self.meta = meta
        self.moz = moz
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

        for step in range(1, self.max_steps + 1):
            resp = self.ai.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )

            if resp.stop_reason != "tool_use":
                answer = "".join(
                    getattr(b, "text", "") for b in resp.content
                    if getattr(b, "type", None) == "text"
                ).strip()
                return AnalystResult(answer=answer, trace=trace, steps=step)

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
                        moz=self.moz,
                    )
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
        )


def _summarize(data: dict) -> str:
    results = data.get("results")
    if isinstance(results, list):
        total = data.get("totalMatchingResults")
        tail = f" of ~{total} total" if total else ""
        return f"{len(results)} rows{tail}"
    return "ok"
