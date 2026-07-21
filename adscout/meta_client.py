"""Meta (Facebook/Instagram) Ad Library client.

SpyFu only sees Google Search ads. Many offers — especially $1-trial /
continuity funnels, info-products, and DTC brands — run primarily on Meta,
which is invisible to SpyFu. This client fills that gap by pulling live ad
creatives from Meta's public Ad Library.

The official Meta Ad Library API only returns political/issue ads (plus EU/UK
commercial ads under the DSA), so US commercial ads are not available there.
We instead drive an Apify Ad Library scraper actor, which reads the public Ad
Library UI and returns commercial ads for any advertiser/keyword/country.

Set APIFY_TOKEN to enable it. The actor is configurable via APIFY_FB_ACTOR
(default: the maintained ``apify/facebook-ads-scraper``).
"""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote_plus

import httpx

APIFY_BASE = "https://api.apify.com/v2"
DEFAULT_ACTOR = "apify~facebook-ads-scraper"  # note: '/' becomes '~' in the API


class MetaError(RuntimeError):
    """Raised for non-retryable Meta/Apify errors (auth, bad request, etc.)."""


def ad_library_search_url(query: str, country: str = "US", active: bool = True) -> str:
    """Build a public Meta Ad Library keyword-search URL."""
    status = "active" if active else "all"
    return (
        "https://www.facebook.com/ads/library/"
        f"?active_status={status}&ad_type=all&country={country or 'US'}"
        f"&q={quote_plus(query)}&search_type=keyword_unordered&media_type=all"
    )


class MetaAdLibraryClient:
    def __init__(
        self,
        settings,
        *,
        mock: bool = False,
        timeout: float = 120.0,
    ) -> None:
        self.settings = settings
        self.mock = mock
        self.actor = os.getenv("APIFY_FB_ACTOR", DEFAULT_ACTOR).replace("/", "~")
        self.token = getattr(settings, "apify_token", None) or os.getenv("APIFY_TOKEN")
        self._http = None if mock else httpx.Client(timeout=timeout)

    # -- public API --------------------------------------------------------

    def search(
        self,
        *,
        query: str | None = None,
        page_url: str | None = None,
        country: str = "US",
        active: bool = True,
        limit: int = 20,
    ) -> dict:
        """Return live/inactive Meta ads for a keyword search or a Page URL."""
        if self.mock:
            return _mock_ads(query or page_url or "offer", limit)

        if not self.token:
            raise MetaError(
                "Meta Ad Library is not configured. Set APIFY_TOKEN to enable "
                "Facebook/Instagram ad lookups (SpyFu only covers Google Search)."
            )

        url = page_url or ad_library_search_url(query or "", country, active)
        payload: dict[str, Any] = {
            "startUrls": [{"url": url}],
            "resultsLimit": max(1, min(limit, 100)),
            "activeStatus": "active" if active else "all",
            "isDetailsPerAd": True,
        }
        endpoint = (f"{APIFY_BASE}/acts/{self.actor}/run-sync-get-dataset-items"
                    f"?token={self.token}")
        try:
            resp = self._http.post(endpoint, json=payload)
        except httpx.RequestError as exc:
            raise MetaError(f"Could not reach the Meta Ad Library scraper: {exc}")

        if resp.status_code in (200, 201):
            items = resp.json()
            if not isinstance(items, list):
                items = items.get("items", []) if isinstance(items, dict) else []
            return {"results": _summarize_ads(items, limit)}
        if resp.status_code in (401, 403):
            raise MetaError("Apify rejected the token (401/403). Check APIFY_TOKEN.")
        raise MetaError(f"Apify {resp.status_code}: {resp.text[:200]}")

    def close(self) -> None:
        if self._http is not None:
            self._http.close()

    def __enter__(self) -> "MetaAdLibraryClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


# --------------------------------------------------------------------------
# Output shaping — compact, token-bounded rows the analyst can cite.
# --------------------------------------------------------------------------

def _summarize_ads(items: list, limit: int) -> list[dict]:
    rows = []
    for it in items[:limit]:
        snap = it.get("snapshot") or {}
        body = (snap.get("body") or {})
        rows.append({
            "pageName": it.get("pageName") or snap.get("pageName"),
            "title": snap.get("title"),
            "body": (body.get("text") or "")[:400],
            "cta": snap.get("ctaText"),
            "linkUrl": snap.get("linkUrl"),
            "startDate": it.get("startDateFormatted") or it.get("startDate"),
            "isActive": it.get("isActive"),
            "platforms": it.get("publisherPlatform") or it.get("publisherPlatforms"),
        })
    return rows


# --------------------------------------------------------------------------
# Mock payload (demo / mock modes — no Apify token or network needed).
# --------------------------------------------------------------------------

def _mock_ads(seed: str, limit: int) -> dict:
    s = (seed or "offer").strip().rstrip("/").split("/")[-1] or "offer"
    ads = [
        {"pageName": "Nail The Mix", "title": f"Master {s} — Mix Real Multitracks",
         "body": "Get the actual stems from #1 records and mix alongside the producer. "
                 "Start for $1. Cancel anytime.",
         "cta": "Sign Up", "linkUrl": "https://nailthemix.com/", "startDate": "2026-05-14",
         "isActive": True, "platforms": ["FACEBOOK", "INSTAGRAM"]},
        {"pageName": "Nail The Mix", "title": "World's Best Education for Metal Producers",
         "body": "Live mixing every month with world-class producers. $1 trial, then $19.99/mo.",
         "cta": "Learn More", "linkUrl": "https://nailthemix.com/join",
         "startDate": "2026-06-02", "isActive": True, "platforms": ["INSTAGRAM"]},
        {"pageName": "Produce Like A Pro", "title": f"Free {s} Masterclass",
         "body": "The 3 mistakes killing your mixes. Free training for home-studio producers.",
         "cta": "Sign Up", "linkUrl": "https://producelikeapro.com/", "startDate": "2026-06-20",
         "isActive": True, "platforms": ["FACEBOOK", "INSTAGRAM", "THREADS"]},
    ]
    return {"resultCount": len(ads), "results": ads[:limit]}
