"""Landing-page screenshot capture via Hexomatic.

Lets the analyst *show* a competitor's landing page or funnel step, not just
describe it — useful when Meta ad creatives point at a tracked landing page or
SpyFu ad history returns a destination URL.

Hexomatic is async (POST -> taskId -> poll GET /result/{taskId}). Measured
latency is ~30-60s for a 2-device capture, so it fits inside an analysis run
provided we bound the wait. Two hard-won details, neither documented:

  * Cloudflare 403s the default python-httpx User-Agent — a browser UA is
    required or every call returns an HTML block page instead of JSON.
  * Responses are array-wrapped, with undocumented keys of the form
    "_device_screenshot_mobile_large".

Set HEXOMATIC_API_KEY to enable.
"""

from __future__ import annotations

import time

import httpx

HEXO_BASE = "https://api.hexomatic.com/tool-api"
SCREENSHOT_AUTOMATION = "screenshot-capture"

# Mobile first (most ad traffic) plus a desktop view.
DEFAULT_DEVICES = ["MOBILE_LARGE", "LAPTOP_LARGE"]
VALID_DEVICES = {
    "MOBILE_SMALL", "MOBILE_MEDIUM", "MOBILE_LARGE", "TABLET",
    "LAPTOP_SMALL", "LAPTOP_MEDIUM", "LAPTOP_LARGE", "DESKTOP_4K",
}

BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


class ScreenshotError(RuntimeError):
    """Raised for non-retryable screenshot/Hexomatic errors."""


def _scalar(value):
    """Hexomatic wraps single values in a list — unwrap them."""
    if isinstance(value, list):
        if len(value) == 1:
            return value[0]
        if not value:
            return None
    return value


class ScreenshotClient:
    def __init__(self, settings, *, mock: bool = False, timeout: float = 30.0) -> None:
        self.settings = settings
        self.mock = mock
        self.token = getattr(settings, "hexomatic_api_key", None)
        self._http = None if mock else httpx.Client(
            timeout=timeout,
            headers={"User-Agent": BROWSER_UA, "Accept": "application/json"},
        )

    # -- public API --------------------------------------------------------

    def capture(self, url: str, *, devices: list[str] | None = None,
                max_wait: int = 120, interval: int = 6) -> dict:
        """Capture `url` and return {"source": url, "images": {device: img_url}}."""
        if self.mock:
            return _mock_capture(url)

        if not self.token:
            raise ScreenshotError(
                "Screenshots are not configured. Set HEXOMATIC_API_KEY to enable "
                "landing-page capture."
            )

        target = url if url.startswith("http") else f"https://{url}"
        devices = [d for d in (devices or DEFAULT_DEVICES) if d in VALID_DEVICES] \
            or DEFAULT_DEVICES

        task_id = self._submit(target, devices)
        images = self._poll(task_id, max_wait=max_wait, interval=interval)
        if not images:
            raise ScreenshotError(
                f"Screenshot of {target} did not finish within {max_wait}s "
                "(the capture may still complete later)."
            )
        return {"source": target, "images": images}

    # -- internals ---------------------------------------------------------

    def _submit(self, target: str, devices: list[str]) -> str:
        payload = {"source": target, "devices": devices, "delay": 5, "adBlock": False}
        try:
            r = self._http.post(
                f"{HEXO_BASE}/{SCREENSHOT_AUTOMATION}?key={self.token}", json=payload)
        except httpx.RequestError as exc:
            raise ScreenshotError(f"Could not reach the screenshot service: {exc}")
        if r.status_code not in (200, 201):
            snippet = r.text[:160].replace("\n", " ")
            raise ScreenshotError(f"Screenshot request failed ({r.status_code}): {snippet}")
        task_id = (r.json() or {}).get("taskId")
        if not task_id:
            raise ScreenshotError("Screenshot service returned no taskId.")
        return task_id

    def _poll(self, task_id: str, *, max_wait: int, interval: int) -> dict:
        deadline = time.time() + max_wait
        while time.time() < deadline:
            try:
                r = self._http.get(f"{HEXO_BASE}/result/{task_id}?key={self.token}")
            except httpx.RequestError:
                time.sleep(interval)
                continue
            if r.status_code == 200:
                try:
                    body = r.json()
                except ValueError:
                    body = None
                images = _extract_images(body)
                if images:
                    return images
            time.sleep(interval)
        return {}

    def close(self) -> None:
        if self._http is not None:
            self._http.close()

    def __enter__(self) -> "ScreenshotClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


# --------------------------------------------------------------------------
# Response shaping
# --------------------------------------------------------------------------

def _extract_images(obj) -> dict:
    """Pull {device: url} out of the (undocumented, array-wrapped) response."""
    found: dict[str, str] = {}

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if isinstance(key, str) and key.startswith("_device_screenshot"):
                    device = key.replace("_device_screenshot_", "") or "view"
                    url = _scalar(value)
                    if isinstance(url, str) and url.startswith("http"):
                        found[device] = url
                else:
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(obj)
    return found


def _mock_capture(url: str) -> dict:
    """Sample capture for demo/mock modes (real Hexomatic-hosted images)."""
    base = "https://storage.googleapis.com/hexomatic-screenshot"
    return {
        "source": url if url.startswith("http") else f"https://{url}",
        "images": {
            "mobile_large": f"{base}/https---nailthemix.com--MobileLarge-1784701617866.png",
            "laptop_large": f"{base}/https---nailthemix.com--Desktop4k-1784701638179.png",
        },
        "note": "sample capture (demo mode)",
    }
