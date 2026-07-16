"""Marketing-analyst tools exposed to Claude.

Each tool is a *curated* view over a SpyFu endpoint: it exposes only the
handful of parameters that matter for answering marketing questions, so the
model routes reliably instead of drowning in 40 raw query params. The
`dispatch` function translates a tool call into a SpyFuClient endpoint call.
"""

from __future__ import annotations

from typing import Any

from .client import SpyFuClient

# Reusable country param schema.
_COUNTRY = {
    "type": "string",
    "description": "Two-letter country/market code (e.g. US, UK, CA, DE). Defaults to US.",
}
_LIMIT = {
    "type": "integer",
    "description": "Max rows to return (1-100).",
    "minimum": 1,
    "maximum": 100,
}

# Tool definitions in the Anthropic Messages `tools` format.
TOOLS: list[dict] = [
    {
        "name": "find_advertisers_for_topic",
        "description": (
            "Find who is actively BUYING ADS in a topic/niche and the keywords they "
            "co-target. Best first call for questions like 'how are people running ads "
            "in the <niche> space' or 'who advertises on <topic>'. Returns keywords with "
            "search volume, cost-per-click, advertiser counts, and a list of advertiser "
            "domains (distinctCompetitors)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Seed topic or keyword, e.g. 'dog food'."},
                "country": _COUNTRY,
                "limit": _LIMIT,
            },
            "required": ["topic"],
        },
    },
    {
        "name": "research_keywords",
        "description": (
            "Explore the keyword space around a topic. Choose a search_type: "
            "'PhraseMatch' (related terms), 'Questions' (what people ask), "
            "'Transactions' (buying-intent terms), 'AlsoRanksFor' (SEO co-ranking), "
            "'AlsoBuysAdsFor' (PPC co-targeting). Returns volume, CPC, difficulty."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Seed keyword/topic."},
                "search_type": {
                    "type": "string",
                    "enum": ["PhraseMatch", "Questions", "Transactions", "AlsoRanksFor", "AlsoBuysAdsFor"],
                    "description": "Which kind of keyword research to run.",
                },
                "min_search_volume": {"type": "integer", "description": "Optional floor on monthly search volume."},
                "country": _COUNTRY,
                "limit": _LIMIT,
            },
            "required": ["topic", "search_type"],
        },
    },
    {
        "name": "get_keyword_ad_history",
        "description": (
            "Show the actual ad creative (headlines + body copy), advertisers, and "
            "landing pages that have run for a SPECIFIC keyword over time. Use to see "
            "HOW advertisers position themselves and what offers/angles they use."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "Exact keyword, e.g. 'grain free dog food'."},
                "country": _COUNTRY,
                "limit": _LIMIT,
            },
            "required": ["keyword"],
        },
    },
    {
        "name": "get_domain_ads",
        "description": (
            "List the paid keywords and ad copy a SPECIFIC domain is running ads on. "
            "Use to profile one advertiser's PPC strategy (e.g. chewy.com)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Advertiser domain, e.g. 'chewy.com'."},
                "include_terms": {"type": "string", "description": "Optional comma-separated terms the keyword must contain."},
                "min_search_volume": {"type": "integer", "description": "Optional floor on monthly search volume."},
                "country": _COUNTRY,
                "limit": _LIMIT,
            },
            "required": ["domain"],
        },
    },
    {
        "name": "get_top_ppc_competitors",
        "description": (
            "Return the top paid-search competitors for a domain, ranked by shared "
            "keyword overlap. Use to map the competitive set around one advertiser."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain to analyze, e.g. 'chewy.com'."},
                "country": _COUNTRY,
                "limit": _LIMIT,
            },
            "required": ["domain"],
        },
    },
    {
        "name": "get_domain_stats",
        "description": (
            "Get a domain's marketing scale: estimated monthly ad budget, paid clicks, "
            "number of ads purchased, average ad rank, and organic clicks. Use to size "
            "up how much an advertiser is spending."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain to analyze."},
                "months": {"type": "integer", "description": "Optional: include the latest N months of history."},
                "country": _COUNTRY,
            },
            "required": ["domain"],
        },
    },
]


def dispatch(client: SpyFuClient, tool_name: str, tool_input: dict, *, default_country: str = "US") -> dict:
    """Execute a tool call against SpyFu and return the raw JSON result."""
    country = tool_input.get("country", default_country)
    limit = tool_input.get("limit", 20)

    if tool_name == "find_advertisers_for_topic":
        return client.call(
            "keyword_expansions",
            query=tool_input["topic"],
            keywordSearchType="AlsoBuysAdsFor",
            countryCode=country,
            pageSize=limit,
            sortBy="SearchVolume",
            sortOrder="Descending",
        )

    if tool_name == "research_keywords":
        return client.call(
            "keyword_expansions",
            query=tool_input["topic"],
            keywordSearchType=tool_input["search_type"],
            countryCode=country,
            pageSize=limit,
            **({"searchVolume.min": tool_input["min_search_volume"]}
               if tool_input.get("min_search_volume") is not None else {}),
        )

    if tool_name == "get_keyword_ad_history":
        return client.call(
            "term_ad_history",
            term=tool_input["keyword"],
            countryCode=country,
            pageSize=limit,
        )

    if tool_name == "get_domain_ads":
        return client.call(
            "paid_serps",
            query=tool_input["domain"],
            countryCode=country,
            pageSize=limit,
            includeTerms=tool_input.get("include_terms"),
            **({"searchVolume.min": tool_input["min_search_volume"]}
               if tool_input.get("min_search_volume") is not None else {}),
        )

    if tool_name == "get_top_ppc_competitors":
        return client.call(
            "top_ppc_competitors",
            domain=tool_input["domain"],
            countryCode=country,
            pageSize=limit,
        )

    if tool_name == "get_domain_stats":
        return client.call(
            "latest_domain_stats",
            domain=tool_input["domain"],
            countryCode=country,
            pastNMonths=tool_input.get("months"),
        )

    raise KeyError(f"Unknown tool '{tool_name}'.")
