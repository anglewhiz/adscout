"""Domain-availability screening via RDAP — the validator's name check.

RDAP is the registries' own public lookup: free, keyless, and fast (~1s per
domain). 404 = unregistered (likely available), 200 = taken. It's a strong
signal but not a purchase guarantee (premium pricing / reserved names can
still surprise at checkout), and it is NOT trademark clearance — the tool's
output says so.

.com/.net go straight to Verisign's RDAP; other TLDs go through rdap.org's
bootstrap router.
"""

from __future__ import annotations

import httpx

VERISIGN = {"com", "net"}


class DomainCheckError(RuntimeError):
    """Raised when the RDAP lookup itself fails (not for 'taken' results)."""


def _rdap_url(domain: str) -> str:
    tld = domain.rsplit(".", 1)[-1].lower()
    if tld in VERISIGN:
        return f"https://rdap.verisign.com/{tld}/v1/domain/{domain}"
    return f"https://rdap.org/domain/{domain}"


class DomainClient:
    MAX_DOMAINS = 10  # per call; each lookup ~1s

    def __init__(self, settings=None, *, mock: bool = False, timeout: float = 10.0) -> None:
        self.mock = mock
        self._http = None if mock else httpx.Client(timeout=timeout, follow_redirects=True)

    def check(self, domains: list[str] | str) -> dict:
        """Check registration status for up to MAX_DOMAINS domains."""
        if isinstance(domains, str):
            domains = [domains]
        cleaned = []
        for d in domains:
            d = str(d).strip().lower().replace("http://", "").replace("https://", "").strip("/")
            if d and "." in d and d not in cleaned:
                cleaned.append(d)
        cleaned = cleaned[:self.MAX_DOMAINS]
        if not cleaned:
            raise DomainCheckError("No valid domain names given (e.g. 'mytool.com').")

        if self.mock:
            return _mock_check(cleaned)

        results = []
        for d in cleaned:
            try:
                r = self._http.get(_rdap_url(d))
                if r.status_code == 404:
                    status = "available"
                elif r.status_code == 200:
                    status = "taken"
                else:
                    status = f"unknown (HTTP {r.status_code})"
            except httpx.RequestError as exc:
                status = f"unknown ({type(exc).__name__})"
            results.append({"domain": d, "status": status})
        return {
            "results": results,
            "note": ("RDAP registration check only — 'available' is a strong signal "
                     "but confirm at the registrar (premium/reserved names exist), "
                     "and this is NOT trademark clearance."),
        }

    def close(self) -> None:
        if self._http is not None:
            self._http.close()

    def __enter__(self) -> "DomainClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def _mock_check(domains: list[str]) -> dict:
    # Deterministic: odd-length second-level labels read as available.
    results = []
    for d in domains:
        label = d.split(".")[0]
        results.append({"domain": d,
                        "status": "available" if len(label) % 2 else "taken"})
    return {"results": results, "note": "sample data (demo mode)"}
