"""Structured product/offer extraction from any e-commerce or landing page URL.

Runs Apify's universal E-commerce Scraping Tool via a saved task. Where a
screenshot shows what a page LOOKS like, this returns what the offer IS:
product names, prices, brand, rating and review counts — machine-readable, so
the analyst can compare a rival's actual pricing/offer structure instead of
eyeballing it. Natural pairing: the landing URL behind a Meta or TikTok ad.

SLOW (~90s measured — it's an AI-extraction crawl), so hard-capped per
analysis. Task slug overridable via APIFY_PRODUCT_TASK.
"""

from __future__ import annotations

import os

import httpx

APIFY_BASE = "https://api.apify.com/v2"
DEFAULT_PRODUCT_TASK = "trevorb55~e-commerce-scraping-tool-task-1"


class ProductError(RuntimeError):
    """Raised for non-retryable product-extraction errors."""


class ProductPageClient:
    MAX_CALLS = 2  # ~90s each

    def __init__(self, settings, *, mock: bool = False, timeout: float = 130.0) -> None:
        self.settings = settings
        self.mock = mock
        self.token = getattr(settings, "apify_token", None) or os.getenv("APIFY_TOKEN")
        self.task = os.getenv("APIFY_PRODUCT_TASK", DEFAULT_PRODUCT_TASK).replace("/", "~")
        self._calls = 0
        self._http = None if mock else httpx.Client(timeout=timeout)

    def extract(self, url: str) -> dict:
        """Extract structured product/offer data from a page URL."""
        target = url if url.startswith("http") else f"https://{url}"
        if self.mock:
            return _mock_extract(target)

        self._calls += 1
        if self._calls > self.MAX_CALLS:
            raise ProductError(
                f"Product-extraction budget reached ({self.MAX_CALLS} per analysis — "
                "each is slow). Conclude with the offer data already gathered.")
        if not self.token:
            raise ProductError(
                "Product extraction is not configured. Set APIFY_TOKEN to enable it.")
        try:
            resp = self._http.post(
                f"{APIFY_BASE}/actor-tasks/{self.task}/run-sync-get-dataset-items"
                f"?token={self.token}",
                json={"listingUrls": [{"url": target}]})
        except httpx.TimeoutException:
            raise ProductError(
                "Product extraction did not finish in time — describe the offer "
                "from the data already gathered rather than retrying.")
        except httpx.RequestError as exc:
            raise ProductError(f"Could not reach the extraction service: {exc}")

        if resp.status_code not in (200, 201):
            raise ProductError(f"Apify {resp.status_code}: {resp.text[:200]}")

        items = resp.json()
        items = items if isinstance(items, list) else []
        rows = []
        for it in items[:10]:
            offers = it.get("offers") or {}
            brand = it.get("brand") or {}
            rows.append({
                "name": it.get("name"),
                "price": offers.get("price"),
                "currency": offers.get("priceCurrency"),
                "brand": (brand.get("name") or brand.get("slogan")
                          if isinstance(brand, dict) else str(brand)[:60]),
                "rating": it.get("rating"),
                "reviewCount": it.get("reviewCount"),
                "url": it.get("url"),
                "description": (it.get("description") or "")[:300],
            })
        return {"source": target, "resultCount": len(rows), "results": rows}

    def close(self) -> None:
        if self._http is not None:
            self._http.close()

    def __enter__(self) -> "ProductPageClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def _mock_extract(url: str) -> dict:
    return {
        "source": url,
        "resultCount": 2,
        "results": [
            {"name": "Flagship Bundle", "price": "149.00", "currency": "USD",
             "brand": "SampleBrand", "rating": 4.7, "reviewCount": 1841, "url": url,
             "description": "Core product plus starter accessories. Free shipping, "
                            "30-day guarantee, subscribe-and-save option at checkout."},
            {"name": "Starter Kit", "price": "49.00", "currency": "USD",
             "brand": "SampleBrand", "rating": 4.5, "reviewCount": 620, "url": url,
             "description": "Entry-level version — the tripwire rung of the ladder."},
        ],
        "note": "sample data (demo mode)",
    }
