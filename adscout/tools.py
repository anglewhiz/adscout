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
    {
        "name": "search_facebook_ads",
        "description": (
            "Find who is advertising a topic/niche on FACEBOOK & INSTAGRAM (Meta), "
            "and see their live ad creatives. SpyFu only covers GOOGLE SEARCH ads, so "
            "use this whenever Google shows little/no paid activity but the offer likely "
            "runs on Meta — typical for $1-trial or continuity funnels, info-products, "
            "coaching, and DTC brands. Returns advertisers, ad copy, CTAs, destination "
            "links, and how long each ad has been running."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Topic, niche, offer, or brand name, e.g. 'metal mixing course'."},
                "active": {"type": "boolean", "description": "Only currently-running ads (default true). Set false to include past ads."},
                "country": _COUNTRY,
                "limit": _LIMIT,
            },
            "required": ["topic"],
        },
    },
    {
        "name": "get_advertiser_facebook_ads",
        "description": (
            "List the Facebook/Instagram (Meta) ads a SPECIFIC advertiser is running, "
            "by their Facebook Page URL or brand/page name. Use to inspect one brand's "
            "Meta ad strategy and creatives (headlines, body copy, offers, CTAs)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "advertiser": {"type": "string", "description": "Facebook Page URL (e.g. https://www.facebook.com/nailthemix) or the brand/page name."},
                "active": {"type": "boolean", "description": "Only currently-running ads (default true)."},
                "country": _COUNTRY,
                "limit": _LIMIT,
            },
            "required": ["advertiser"],
        },
    },
    {
        "name": "generate_creative",
        "description": (
            "GENERATE the VISUAL for a new ad creative or landing-page hero mockup, using "
            "what you learned about the niche. Use only when the user asks to create / "
            "design / mock up an ad or landing page for THEIR offer — this MAKES new "
            "visuals, it does not research existing ones (use search_facebook_ads for "
            "competitors' real ads, capture_landing_page to screenshot a real page). "
            "Write the actual ad COPY (headlines, primary text, offer, CTA) in your "
            "answer's '## Ad concepts' section using the ad-copy rules; here in `brief` "
            "describe only the IMAGE — scene, subject, mood, composition — and leave "
            "clean space for a headline (image models render text poorly, so don't rely "
            "on baked-in text). The image is shown to the user automatically; never paste "
            "the image URL. Costs credits: at most 2 calls per answer."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "brief": {"type": "string", "description": "Detailed visual prompt: scene, subject, style, mood, composition, any text to appear."},
                "format": {
                    "type": "string",
                    "enum": ["ad_square", "ad_story", "ad_landscape", "landing_hero"],
                    "description": "ad_square = feed; ad_story = vertical reels/stories; ad_landscape = in-feed landscape; landing_hero = landing-page hero banner.",
                },
                "count": {"type": "integer", "description": "How many variants (1-3). Default 1.", "minimum": 1, "maximum": 3},
                "label": {"type": "string", "description": "Short caption, e.g. 'Meal-kit ad concept - convenience angle'."},
            },
            "required": ["brief"],
        },
    },
    {
        "name": "capture_landing_page",
        "description": (
            "Take a real SCREENSHOT of a landing page or funnel step so the user can "
            "SEE it (mobile + desktop). Use for the single most important destination "
            "page in the answer — e.g. the landing page a Meta ad points to "
            "(the linkUrl from search_facebook_ads), a funnel/sample/order page, or a "
            "competitor's offer page. The image is shown to the user automatically, so "
            "just mention what the page shows; do NOT paste the image URL. "
            "SLOW (~30-60s) and costs credits: call it at most 1-2 times per answer, "
            "and only when seeing the page adds real value."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Full URL of the page to capture."},
                "label": {"type": "string", "description": "Short caption, e.g. 'Factor - 50% off landing page'."},
            },
            "required": ["url"],
        },
    },
    {
        "name": "get_seo_authority",
        "description": (
            "Get a domain's ORGANIC SEO strength from Moz: Domain Authority (0-100), "
            "Page Authority, spam score, number of linking root domains, and total "
            "inbound links. Use to judge how established/credible a site is, how hard "
            "it would be to outrank, or whether a brand is a real operator vs thin. "
            "Complements the ad data (SpyFu = Google ads, Meta = Facebook ads)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain to analyze, e.g. 'chewy.com'."},
            },
            "required": ["domain"],
        },
    },
    {
        "name": "get_linking_domains",
        "description": (
            "List the highest-authority websites that LINK TO a domain (its backlink "
            "sources), from Moz. Use to see where a competitor earns authority from — "
            "press, partners, directories, communities — and to find link opportunities."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain to analyze."},
                "limit": _LIMIT,
            },
            "required": ["domain"],
        },
    },
    {
        "name": "get_top_pages",
        "description": (
            "List a domain's strongest pages by link equity (Moz): URL, title, Page "
            "Authority, and how many root domains link to each. Use to see which "
            "content actually earns links and drives a competitor's organic presence."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain to analyze."},
                "limit": _LIMIT,
            },
            "required": ["domain"],
        },
    },
]


def dispatch(client: SpyFuClient, tool_name: str, tool_input: dict, *,
             default_country: str = "US", meta=None, moz=None, shots=None,
             creative=None) -> dict:
    """Execute a tool call and return the raw JSON result.

    SpyFu (Google Search) tools use ``client``; Meta (Facebook/Instagram) tools
    use ``meta`` (a MetaAdLibraryClient); Moz (SEO authority/backlinks) tools
    use ``moz`` (a MozClient). ``meta``/``moz`` may be None when unavailable.
    """
    country = tool_input.get("country", default_country)
    limit = tool_input.get("limit", 20)

    # -- Creative generation (fal.ai) --------------------------------------
    if tool_name == "generate_creative":
        if creative is None:
            return {"error": "Creative generation is not available in this run "
                             "(set FAL_KEY to enable it)."}
        try:
            data = creative.generate(
                tool_input["brief"],
                fmt=tool_input.get("format", "ad_square"),
                count=tool_input.get("count", 1),
            )
        except Exception as exc:
            return {"error": str(exc)}
        data["label"] = tool_input.get("label") or tool_input["brief"][:60]
        data["_generated_creative"] = True
        return data

    # -- Landing-page screenshot ------------------------------------------
    if tool_name == "capture_landing_page":
        if shots is None:
            return {"error": "Screenshots are not available in this run "
                             "(set HEXOMATIC_API_KEY to enable them)."}
        try:
            data = shots.capture(tool_input["url"])
        except Exception as exc:
            return {"error": str(exc)}
        data["label"] = tool_input.get("label") or tool_input["url"]
        # Marker the analyst loop looks for when collecting images for the UI.
        data["_captured_screenshot"] = True
        return data

    # -- Moz (SEO authority / backlinks) ----------------------------------
    if tool_name in ("get_seo_authority", "get_linking_domains", "get_top_pages"):
        if moz is None:
            return {"error": "SEO authority lookups are not available in this run "
                             "(set MOZ_ACCESS_ID / MOZ_SECRET_KEY to enable them)."}
        domain = tool_input["domain"]
        if tool_name == "get_seo_authority":
            return moz.url_metrics(domain)
        if tool_name == "get_linking_domains":
            return moz.linking_domains(domain, limit=limit)
        return moz.top_pages(domain, limit=limit)

    # -- Meta (Facebook/Instagram) Ad Library -----------------------------
    if tool_name in ("search_facebook_ads", "get_advertiser_facebook_ads"):
        if meta is None:
            return {"error": "Facebook/Meta ad lookups are not available in this run "
                             "(set APIFY_TOKEN to enable them)."}
        active = tool_input.get("active", True)
        if tool_name == "search_facebook_ads":
            return meta.search(query=tool_input["topic"], country=country,
                               active=active, limit=limit)
        advertiser = tool_input["advertiser"].strip()
        if advertiser.startswith("http://") or advertiser.startswith("https://"):
            return meta.search(page_url=advertiser, country=country,
                               active=active, limit=limit)
        return meta.search(query=advertiser, country=country,
                           active=active, limit=limit)

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
