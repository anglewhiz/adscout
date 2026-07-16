"""
SpyFu endpoint registry.

Every entry here was verified against SpyFu's published OpenAPI definitions
(https://developer.spyfu.com/llms.txt and the per-endpoint `.md` specs).

The important, non-obvious detail about the SpyFu API: the *server segment*
and the *operation path* are separate, and the server segment is NOT derivable
from the docs URL slug. For example:

    docs slug: adhistoryapi_gettermadhistory
    real URL : https://api.spyfu.com/apis/cloud_ad_history_api/v2/term/getTermAdHistory
                                          ^^^^^^^^^^^^^^^^^^^^^  <- "cloud_" prefix, unguessable

So each endpoint stores the exact `server` + `path`. To add a new endpoint,
open its `.md` page on developer.spyfu.com, copy `servers[0].url` into `server`
and the path key into `path`, and add it below.
"""

from dataclasses import dataclass, field
from typing import Any, Callable

BASE_URL = "https://api.spyfu.com"

# Two-letter country codes SpyFu accepts (maps to the Google domain queried).
COUNTRY_CODES = [
    "AR", "AT", "AU", "BE", "BR", "CA", "CH", "DE", "DK", "ES", "FR", "IE",
    "IN", "IT", "JP", "MX", "NL", "NO", "NZ", "PL", "PT", "SE", "SG", "TR",
    "UA", "UK", "US", "ZA",
]


@dataclass(frozen=True)
class Endpoint:
    """A single verified SpyFu REST endpoint."""
    name: str            # internal key
    server: str          # e.g. "apis/serp_api"  (the OpenAPI servers[0].url tail)
    path: str            # e.g. "/v2/ppc/getPaidSerps"
    required: tuple      # required query-param names
    doc: str             # one-line description
    # Builds a small, deterministic fake payload for --mock / offline testing.
    mock: Callable[[dict], dict] = field(default=lambda params: {"results": []})

    def url(self) -> str:
        return f"{BASE_URL}/{self.server.strip('/')}{self.path}"


# --------------------------------------------------------------------------
# Mock payload builders (offline mode only — shapes mirror the real responses)
# --------------------------------------------------------------------------

def _mock_keyword_expansions(p: dict) -> dict:
    q = p.get("query", "seed")
    return {
        "resultCount": 3,
        "totalMatchingResults": 812,
        "results": [
            {"keyword": f"best {q}", "searchVolume": 74000, "broadCostPerClick": 1.42,
             "paidCompetitors": 18, "distinctCompetitors": ["chewy.com", "petsmart.com", "amazon.com"]},
            {"keyword": f"grain free {q}", "searchVolume": 33100, "broadCostPerClick": 2.05,
             "paidCompetitors": 12, "distinctCompetitors": ["chewy.com", "thefarmersdog.com"]},
            {"keyword": f"{q} delivery", "searchVolume": 12100, "broadCostPerClick": 3.10,
             "paidCompetitors": 9, "distinctCompetitors": ["thefarmersdog.com", "ollie.com"]},
        ],
    }


def _mock_term_ad_history(p: dict) -> dict:
    t = p.get("term", "keyword")
    return {
        "resultCount": 2,
        "results": [
            {"domainName": "chewy.com", "position": 1, "searchDateId": 20260115,
             "title": f"{t.title()} - Free 1-2 Day Shipping",
             "body": "Shop premium brands. Autoship & save 35% on your first order.",
             "urls": ["https://www.chewy.com/b/food"]},
            {"domainName": "thefarmersdog.com", "position": 2, "searchDateId": 20260114,
             "title": "Fresh Dog Food, Delivered",
             "body": "Human-grade, vet-developed recipes. Personalized plans. 50% off trial.",
             "urls": ["https://www.thefarmersdog.com/"]},
        ],
    }


def _mock_paid_serps(p: dict) -> dict:
    d = p.get("query", "example.com")
    return {
        "resultCount": 2,
        "totalMatchingResults": 4200,
        "results": [
            {"keyword": "dog food", "domain": d, "adPosition": 1, "searchVolume": 673000,
             "keywordDifficulty": 71, "title": "Premium Dog Food - Shop Now",
             "bodyHtml": "Free shipping over $49. Autoship & save."},
            {"keyword": "puppy food", "domain": d, "adPosition": 2, "searchVolume": 90500,
             "keywordDifficulty": 63, "title": "Puppy Food, Vet Recommended",
             "bodyHtml": "Grain-free recipes. Delivered to your door."},
        ],
    }


def _mock_top_ppc_competitors(p: dict) -> dict:
    return {
        "resultCount": 3,
        "totalMatchingResults": 240,
        "results": [
            {"domain": "chewy.com", "commonTerms": 1432, "rank": 0.91},
            {"domain": "petsmart.com", "commonTerms": 1105, "rank": 0.78},
            {"domain": "petco.com", "commonTerms": 980, "rank": 0.71},
        ],
    }


def _mock_domain_stats(p: dict) -> dict:
    d = p.get("domain", "example.com")
    return {
        "domain": d,
        "resultCount": 1,
        "results": [
            {"searchMonth": 1, "searchYear": 2026, "monthlyBudget": 812443.0,
             "monthlyPaidClicks": 240113.0, "totalAdsPurchased": 5871,
             "averageAdRank": 1.4, "monthlyOrganicClicks": 1904221.0,
             "totalOrganicResults": 410233, "strength": 88},
        ],
    }


# --------------------------------------------------------------------------
# The registry
# --------------------------------------------------------------------------

ENDPOINTS: dict[str, Endpoint] = {
    "keyword_expansions": Endpoint(
        name="keyword_expansions",
        server="apis/keyword_api",
        path="/v2/related/getKeywordExpansions",
        required=("query", "keywordSearchType"),
        doc="Keyword research of 5 kinds (PhraseMatch, Questions, AlsoBuysAdsFor, "
            "AlsoRanksFor, Transactions). Returns volume, CPC, and advertiser lists.",
        mock=_mock_keyword_expansions,
    ),
    "term_ad_history": Endpoint(
        name="term_ad_history",
        server="apis/cloud_ad_history_api",
        path="/v2/term/getTermAdHistory",
        required=("term",),
        doc="Historical advertisers and ad copy (title/body/landing pages) for a keyword.",
        mock=_mock_term_ad_history,
    ),
    "paid_serps": Endpoint(
        name="paid_serps",
        server="apis/serp_api",
        path="/v2/ppc/getPaidSerps",
        required=("query",),
        doc="Paid keywords/ads a specific domain appears on, with ad copy and positions.",
        mock=_mock_paid_serps,
    ),
    "top_ppc_competitors": Endpoint(
        name="top_ppc_competitors",
        server="apis/competitors_api",
        path="/v2/ppc/getTopCompetitors",
        required=("domain",),
        doc="Top paid-search competitors for a domain by shared-keyword overlap.",
        mock=_mock_top_ppc_competitors,
    ),
    "latest_domain_stats": Endpoint(
        name="latest_domain_stats",
        server="apis/domain_stats_api",
        path="/v2/getLatestDomainStats",
        required=("domain",),
        doc="Latest monthly stats for a domain: ad budget, paid clicks, ads purchased, "
            "organic clicks, strength. Optional pastNMonths for a short history.",
        mock=_mock_domain_stats,
    ),
    # The endpoint the project started from (same server as latest, full history).
    "all_domain_stats": Endpoint(
        name="all_domain_stats",
        server="apis/domain_stats_api",
        path="/v2/getAllDomainStats",
        required=("domain",),
        doc="Full time-series of monthly SEO/PPC stats for a domain across all periods.",
        mock=_mock_domain_stats,
    ),
}
