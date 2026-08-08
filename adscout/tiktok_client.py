"""TikTok intelligence via Apify tasks: Shop commerce data + ad creatives.

Two saved Apify tasks (configured in the user's Apify account) power a TikTok
channel that neither SpyFu nor the Meta Ad Library covers:

  * TikTok Shop scraper — keyword -> products with unitsSold, sale/original
    price, rating and seller. soldCount x salePrice gives an estimated-revenue
    ranking; seller concentration, discount patterns and price-band clustering
    fall straight out of the rows.
  * TikTok ads scraper — query -> ad creatives WITH impressions, spend ranges,
    run dates and age/gender targeting (performance data Meta's library omits).

Both run through Apify's synchronous task API and are SLOW (~60-100s measured),
so calls are hard-capped per analysis and the analyst's wall-clock guard covers
them. Task slugs are overridable via APIFY_TIKTOK_SHOP_TASK / APIFY_TIKTOK_ADS_TASK.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

APIFY_BASE = "https://api.apify.com/v2"
DEFAULT_SHOP_TASK = "trevorb55~tiktok-shop-scraper-task"
DEFAULT_ADS_TASK = "trevorb55~tiktok-ads-scraper-task"


class TikTokError(RuntimeError):
    """Raised for non-retryable TikTok/Apify errors."""


def _num(value) -> float | None:
    # Prices arrive either as scalars or as {"value": 10.39, "currency": "USD"}.
    if isinstance(value, dict):
        value = value.get("value")
    try:
        return float(str(value).replace("$", "").replace(",", ""))
    except (TypeError, ValueError):
        return None


def summarize_shop_items(items: list, limit: int) -> dict:
    """Compact, revenue-ranked rows from raw TikTok Shop scraper output."""
    rows = []
    for it in items:
        sold = _num(it.get("soldCount")) or 0
        price = _num(it.get("salePrice"))
        orig = _num(it.get("originalPrice"))
        seller = it.get("seller") or {}
        rating = it.get("rating") or {}
        labels = it.get("labels") or []
        rows.append({
            "title": (it.get("title") or "")[:120],
            "salePrice": price,
            "originalPrice": orig,
            "discounted": bool((orig and price and orig > price)
                               or any("deal" in str(l).lower() for l in labels)),
            "labels": [str(l) for l in labels[:3]],
            "soldCount": int(sold),
            "estRevenue": round(sold * price) if price else None,
            "rating": rating.get("score") if isinstance(rating, dict) else rating,
            "reviewCount": rating.get("reviewCount") if isinstance(rating, dict) else None,
            "seller": (seller.get("shopName") or seller.get("name")
                       or str(seller)[:60] if seller else None),
            "productUrl": it.get("productUrl"),
        })
    rows.sort(key=lambda r: r["estRevenue"] or 0, reverse=True)
    return {"resultCount": len(rows), "results": rows[:max(1, limit * 3)]}


class TikTokClient:
    # Combined cap across shop+ads per analysis — each call is ~60-100s.
    MAX_CALLS = 2

    def __init__(self, settings, *, mock: bool = False, timeout: float = 130.0) -> None:
        self.settings = settings
        self.mock = mock
        self.token = getattr(settings, "apify_token", None) or os.getenv("APIFY_TOKEN")
        self.shop_task = os.getenv("APIFY_TIKTOK_SHOP_TASK", DEFAULT_SHOP_TASK).replace("/", "~")
        self.ads_task = os.getenv("APIFY_TIKTOK_ADS_TASK", DEFAULT_ADS_TASK).replace("/", "~")
        self._calls = 0
        self._http = None if mock else httpx.Client(timeout=timeout)

    # -- internals ---------------------------------------------------------

    def _run_task(self, task: str, payload: dict) -> list:
        self._calls += 1
        if self._calls > self.MAX_CALLS:
            raise TikTokError(
                f"TikTok lookup budget reached ({self.MAX_CALLS} per analysis — each "
                "is slow). Conclude with the TikTok data already gathered.")
        if not self.token:
            raise TikTokError(
                "TikTok lookups are not configured. Set APIFY_TOKEN to enable them.")
        try:
            resp = self._http.post(
                f"{APIFY_BASE}/actor-tasks/{task}/run-sync-get-dataset-items"
                f"?token={self.token}", json=payload)
        except httpx.TimeoutException:
            raise TikTokError(
                "The TikTok scrape did not finish in time — conclude with the data "
                "already gathered rather than retrying.")
        except httpx.RequestError as exc:
            raise TikTokError(f"Could not reach the TikTok scraper: {exc}")

        if resp.status_code in (200, 201):
            items = resp.json()
            return items if isinstance(items, list) else []
        if resp.status_code in (401, 403):
            try:
                detail = ((resp.json() or {}).get("error") or {}).get("message", "")
            except ValueError:
                detail = resp.text[:150]
            raise TikTokError(
                f"Apify {resp.status_code}: {detail or 'token rejected'} — if the "
                "token is valid, the monthly usage limit is likely exhausted.")
        raise TikTokError(f"Apify {resp.status_code}: {resp.text[:200]}")

    # -- public API --------------------------------------------------------

    def shop(self, keywords: list[str] | str, *, limit: int = 12) -> dict:
        """TikTok Shop products for ONE keyword, with revenue estimation built in.

        Runtime scales with total products scraped (1 keyword x ~12 products is
        ~75-90s; three keywords blew the serverless window in production), so
        only the FIRST keyword is used — additional coverage comes from a second
        call within the per-analysis budget.
        """
        if isinstance(keywords, str):
            keywords = [keywords]
        keywords = [k.strip() for k in keywords if k and k.strip()][:1]
        if not keywords:
            raise TikTokError("No keyword given for the TikTok Shop lookup.")
        limit = max(1, min(int(limit or 12), 15))
        if self.mock:
            return _mock_shop(keywords, limit)

        items = self._run_task(self.shop_task,
                               {"keywords": keywords, "productsPerSearch": limit})
        return summarize_shop_items(items, limit)

    def ads(self, query: str, *, limit: int = 15) -> dict:
        """TikTok ad creatives for a query, with impressions/spend/targeting."""
        if self.mock:
            return _mock_ads(query, limit)

        items = self._run_task(self.ads_task, {"query": query})
        rows = []
        for it in items[:max(1, min(int(limit or 15), 30))]:
            targeting = []
            if it.get("targetingByAge"):
                targeting.append(f"age {it['targetingByAge']}")
            if it.get("targetingByGender"):
                targeting.append(str(it["targetingByGender"]))
            rows.append({
                "advertiser": it.get("advertiserName"),
                "title": (it.get("adTitle") or "")[:150],
                "impressions": it.get("adImpressions"),
                "spent": it.get("adSpent"),
                "startDate": it.get("adStartDate"),
                "endDate": it.get("adEndDate"),
                "landingUrl": (it.get("adLandingUrl") or "")[:180] or None,
                "status": it.get("status"),
                "targeting": ", ".join(str(t) for t in targeting) or None,
            })
        return {"resultCount": len(rows), "results": rows}

    def close(self) -> None:
        if self._http is not None:
            self._http.close()

    def __enter__(self) -> "TikTokClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


# --------------------------------------------------------------------------
# Mock payloads (demo / mock modes)
# --------------------------------------------------------------------------

def _mock_shop(keywords: list[str], limit: int) -> dict:
    k = (keywords or ["product"])[0]
    rows = [
        {"title": f"Premium {k} — Best Seller", "salePrice": 19.99, "originalPrice": 19.99,
         "discounted": False, "soldCount": 48200, "estRevenue": 963518, "rating": 4.8,
         "seller": "TopBrand Official", "productUrl": "https://shop.tiktok.com/us/pdp/mock1"},
        {"title": f"Budget {k} 2-Pack", "salePrice": 9.99, "originalPrice": 14.99,
         "discounted": True, "soldCount": 12100, "estRevenue": 120879, "rating": 4.5,
         "seller": "ValueDeals Store", "productUrl": "https://shop.tiktok.com/us/pdp/mock2"},
        {"title": f"Pro {k} Kit with Accessories", "salePrice": 34.99, "originalPrice": 49.99,
         "discounted": True, "soldCount": 3300, "estRevenue": 115467, "rating": 4.7,
         "seller": "TopBrand Official", "productUrl": "https://shop.tiktok.com/us/pdp/mock3"},
    ]
    return {"resultCount": min(len(rows), limit), "results": rows[:limit],
            "note": "sample data (demo mode)"}


def _mock_ads(query: str, limit: int) -> dict:
    rows = [
        {"advertiser": "TopBrand Official", "title": f"The {query} everyone's talking about",
         "impressions": "1M-2M", "spent": "$10K-$20K", "startDate": "2026-06-01",
         "endDate": "2026-07-20", "landingUrl": "https://topbrand.com/offer",
         "status": "active", "targeting": "age 25-44, female-skewed"},
        {"advertiser": "ChallengerCo", "title": f"Why I switched my {query} routine",
         "impressions": "100K-500K", "spent": "$1K-$5K", "startDate": "2026-07-01",
         "endDate": None, "landingUrl": "https://challengerco.com/lp",
         "status": "active", "targeting": "age 18-34"},
    ]
    return {"resultCount": min(len(rows), limit), "results": rows[:limit],
            "note": "sample data (demo mode)"}
