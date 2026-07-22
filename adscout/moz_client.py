"""Moz API client — SEO authority and backlink intelligence.

Third data channel for AdSherlock. SpyFu covers Google *paid* search, Meta
covers Facebook/Instagram ad creatives; Moz covers the *organic authority*
side: Domain Authority, spam score, who links to a site, and which of its
pages carry the most link equity.

Moz Links API v2:
    base : https://lsapi.seomoz.com/v2/
    auth : HTTP Basic, base64("AccessID:SecretKey") — no token expiry
    creds: Moz Pro -> Account Settings -> API Access

Set MOZ_ACCESS_ID and MOZ_SECRET_KEY to enable it.
"""

from __future__ import annotations

import base64
from typing import Any

import httpx

MOZ_BASE = "https://lsapi.seomoz.com/v2"


class MozError(RuntimeError):
    """Raised for non-retryable Moz API errors (auth, bad request, quota)."""


class MozClient:
    def __init__(self, settings, *, mock: bool = False, timeout: float = 30.0) -> None:
        self.settings = settings
        self.mock = mock
        self.access_id = getattr(settings, "moz_access_id", None)
        self.secret_key = getattr(settings, "moz_secret_key", None)
        self._http = None if mock else httpx.Client(timeout=timeout)

    # -- internals ---------------------------------------------------------

    def _auth_header(self) -> str:
        if not (self.access_id and self.secret_key):
            raise MozError(
                "Moz is not configured. Set MOZ_ACCESS_ID and MOZ_SECRET_KEY "
                "(Moz Pro -> Account Settings -> API Access) to enable SEO "
                "authority and backlink lookups."
            )
        raw = f"{self.access_id.strip()}:{self.secret_key.strip()}".encode()
        return "Basic " + base64.b64encode(raw).decode()

    def _post(self, endpoint: str, payload: dict) -> dict:
        url = f"{MOZ_BASE}/{endpoint}"
        try:
            resp = self._http.post(
                url, json=payload,
                headers={"Authorization": self._auth_header(),
                         "Content-Type": "application/json"},
            )
        except httpx.RequestError as exc:
            raise MozError(f"Could not reach Moz: {exc}")

        if resp.status_code == 200:
            return resp.json()
        if resp.status_code in (401, 403):
            raise MozError(
                f"{resp.status_code} from Moz — check MOZ_ACCESS_ID / "
                f"MOZ_SECRET_KEY. Details: {resp.text[:200]}"
            )
        if resp.status_code == 429:
            raise MozError("429 from Moz — API quota/rate limit reached.")
        raise MozError(f"Moz {resp.status_code}: {resp.text[:250]}")

    # -- public API --------------------------------------------------------

    def url_metrics(self, domain: str) -> dict:
        """Domain Authority, Page Authority, spam score, link counts."""
        if self.mock:
            return _mock_url_metrics(domain)
        data = self._post("url_metrics", {"targets": [domain]})
        rows = data.get("results") or []
        return {"results": [_shape_metrics(r) for r in rows]}

    def top_pages(self, domain: str, limit: int = 10) -> dict:
        """The domain's pages carrying the most link equity."""
        if self.mock:
            return _mock_top_pages(domain, limit)
        data = self._post("top_pages", {
            "target": domain, "scope": "root_domain",
            "limit": max(1, min(limit, 50)),
        })
        rows = data.get("results") or []
        return {"results": [{
            "page": r.get("page"),
            "title": r.get("title"),
            "page_authority": r.get("page_authority"),
            "linking_root_domains": r.get("root_domains_to_page"),
            "http_code": r.get("http_code"),
        } for r in rows[:limit]]}

    def linking_domains(self, domain: str, limit: int = 10) -> dict:
        """Top root domains linking to the target, by authority."""
        if self.mock:
            return _mock_linking_domains(domain, limit)
        data = self._post("linking_root_domains", {
            "target": domain, "target_scope": "root_domain",
            "limit": max(1, min(limit, 50)), "sort": "domain_authority",
        })
        rows = data.get("results") or []
        return {"results": [{
            "root_domain": r.get("root_domain"),
            "domain_authority": r.get("domain_authority"),
        } for r in rows[:limit]]}

    def close(self) -> None:
        if self._http is not None:
            self._http.close()

    def __enter__(self) -> "MozClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


# --------------------------------------------------------------------------
# Output shaping
# --------------------------------------------------------------------------

def _shape_metrics(r: dict) -> dict:
    return {
        "page": r.get("page"),
        "domain_authority": r.get("domain_authority"),
        "page_authority": r.get("page_authority"),
        "spam_score": r.get("spam_score"),
        "linking_root_domains": r.get("root_domains_to_root_domain"),
        "total_inbound_links": r.get("pages_to_root_domain"),
        "last_crawled": r.get("last_crawled"),
        "title": r.get("title"),
    }


# --------------------------------------------------------------------------
# Mock payloads (demo / mock modes — no credentials or network needed)
# --------------------------------------------------------------------------

def _mock_url_metrics(domain: str) -> dict:
    return {"results": [{
        "page": domain, "domain_authority": 54, "page_authority": 48,
        "spam_score": 2, "linking_root_domains": 1840,
        "total_inbound_links": 96500, "last_crawled": "2026-07-10",
        "title": domain,
    }]}


def _mock_top_pages(domain: str, limit: int) -> dict:
    rows = [
        {"page": f"{domain}/", "title": "Home", "page_authority": 48,
         "linking_root_domains": 910, "http_code": 200},
        {"page": f"{domain}/blog/best-guide", "title": "The Complete Guide",
         "page_authority": 41, "linking_root_domains": 260, "http_code": 200},
        {"page": f"{domain}/pricing", "title": "Pricing",
         "page_authority": 33, "linking_root_domains": 74, "http_code": 200},
    ]
    return {"results": rows[:limit]}


def _mock_linking_domains(domain: str, limit: int) -> dict:
    rows = [
        {"root_domain": "nytimes.com", "domain_authority": 94},
        {"root_domain": "reddit.com", "domain_authority": 91},
        {"root_domain": "wikipedia.org", "domain_authority": 98},
        {"root_domain": "medium.com", "domain_authority": 95},
    ]
    return {"results": rows[:limit]}
