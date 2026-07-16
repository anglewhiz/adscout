"""HTTP client for the SpyFu API.

Handles Basic auth, retries with backoff (respecting Retry-After on 429),
None-stripping of params, and an offline `mock` mode so the whole tool can be
demoed and tested without credentials or network access.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from .config import Settings
from .endpoints import ENDPOINTS, Endpoint


class SpyFuError(RuntimeError):
    """Raised for non-retryable SpyFu API errors (auth, bad request, etc.)."""


class SpyFuClient:
    def __init__(
        self,
        settings: Settings,
        *,
        mock: bool = False,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        self.settings = settings
        self.mock = mock
        self.timeout = timeout
        self.max_retries = max_retries
        self._http = None if mock else httpx.Client(timeout=timeout)

    # -- public API --------------------------------------------------------

    def call(self, endpoint_name: str, **params: Any) -> dict:
        """Call a registered endpoint by name with query params.

        None-valued params are dropped. Returns the parsed JSON body.
        """
        if endpoint_name not in ENDPOINTS:
            raise KeyError(f"Unknown endpoint '{endpoint_name}'.")
        endpoint = ENDPOINTS[endpoint_name]

        clean = {k: v for k, v in params.items() if v is not None}
        missing = [r for r in endpoint.required if r not in clean]
        if missing:
            raise SpyFuError(
                f"{endpoint_name} is missing required parameter(s): {', '.join(missing)}"
            )

        if self.mock:
            return endpoint.mock(clean)

        return self._request(endpoint, clean)

    def close(self) -> None:
        if self._http is not None:
            self._http.close()

    def __enter__(self) -> "SpyFuClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # -- internals ---------------------------------------------------------

    def _headers(self) -> dict:
        return {
            "Authorization": f"Basic {self.settings.basic_auth_token()}",
            "Accept": "application/json",
        }

    def _request(self, endpoint: Endpoint, params: dict) -> dict:
        url = endpoint.url()
        headers = self._headers()
        last_exc: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                resp = self._http.get(url, params=params, headers=headers)
            except httpx.RequestError as exc:  # network hiccup -> retry
                last_exc = exc
                self._sleep_backoff(attempt)
                continue

            if resp.status_code == 200:
                return resp.json()

            if resp.status_code == 401:
                raise SpyFuError(
                    "401 Unauthorized — check SPYFU_API_ID / SPYFU_SECRET_KEY and that "
                    "your plan includes API access (Pro+AI or Team/Agency)."
                )
            if resp.status_code == 400:
                raise SpyFuError(f"400 Bad Request for {url} with params={params}: {resp.text[:300]}")
            if resp.status_code == 429 or resp.status_code >= 500:
                # Retryable. Honor Retry-After when present.
                retry_after = resp.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    time.sleep(min(int(retry_after), 30))
                else:
                    self._sleep_backoff(attempt)
                last_exc = SpyFuError(f"{resp.status_code} from SpyFu: {resp.text[:200]}")
                continue

            raise SpyFuError(f"Unexpected {resp.status_code} from {url}: {resp.text[:300]}")

        raise SpyFuError(f"Request to {url} failed after retries: {last_exc}")

    @staticmethod
    def _sleep_backoff(attempt: int) -> None:
        time.sleep(min(2 ** attempt, 8))

    # -- convenience: pull more than one page ------------------------------

    def paginate(
        self,
        endpoint_name: str,
        *,
        page_size: int = 50,
        max_rows: int = 200,
        **params: Any,
    ) -> list[dict]:
        """Fetch up to `max_rows` result rows across pages via startingRow.

        Works for endpoints that expose pageSize/startingRow (most list endpoints).
        """
        rows: list[dict] = []
        starting_row = 1
        while len(rows) < max_rows:
            batch = self.call(
                endpoint_name,
                pageSize=min(page_size, max_rows - len(rows)),
                startingRow=starting_row,
                **params,
            )
            results = batch.get("results") or []
            if not results:
                break
            rows.extend(results)
            if len(results) < page_size:
                break
            starting_row += len(results)
        return rows[:max_rows]
