"""Creative generation via fal.ai — turn competitive intel into visuals.

The rest of AdSherlock answers "what are competitors running?". This closes the
loop: once the analyst knows the offers, angles and landing pages in a niche, it
can generate actual ad creatives and landing-page hero mockups for the user's
own angle.

fal.ai runs generative image models behind a simple synchronous REST API:

    POST https://fal.run/<model-id>
    Authorization: Key <FAL_KEY>
    {"prompt": ..., "image_size": ..., "num_images": N}
    -> {"images": [{"url", "width", "height", "content_type"}], "seed", ...}

Unlike the Hexomatic screenshot flow there is no polling — fal.run returns the
result directly, typically in a couple of seconds.

Default model is FLUX.1 [schnell]: fast and cheap, which matters because this
runs inside an interactive analysis. Override with FAL_MODEL.
"""

from __future__ import annotations

import os

import httpx

FAL_BASE = "https://fal.run"
DEFAULT_MODEL = "fal-ai/flux/schnell"

# Friendly format names -> fal image_size values.
FORMATS = {
    "ad_square": "square_hd",        # feed / carousel
    "ad_story": "portrait_16_9",     # stories, reels, vertical video frames
    "ad_landscape": "landscape_4_3",  # in-feed landscape
    "landing_hero": "landscape_16_9",  # landing-page hero banner
}
DEFAULT_FORMAT = "ad_square"
MAX_IMAGES = 3


class CreativeError(RuntimeError):
    """Raised for non-retryable creative-generation errors."""


class CreativeClient:
    def __init__(self, settings, *, mock: bool = False, timeout: float = 90.0) -> None:
        self.settings = settings
        self.mock = mock
        self.key = getattr(settings, "fal_key", None)
        self.model = os.getenv("FAL_MODEL", DEFAULT_MODEL)
        self._http = None if mock else httpx.Client(timeout=timeout)

    def generate(self, brief: str, *, fmt: str = DEFAULT_FORMAT, count: int = 1) -> dict:
        """Generate image(s) from `brief`; returns {"format","brief","images":[...]}"""
        fmt = fmt if fmt in FORMATS else DEFAULT_FORMAT
        count = max(1, min(int(count or 1), MAX_IMAGES))

        if self.mock:
            return _mock_generate(brief, fmt, count)

        if not self.key:
            raise CreativeError(
                "Creative generation is not configured. Set FAL_KEY to enable "
                "ad-creative and landing-page mockup generation."
            )

        payload = {
            "prompt": brief,
            "image_size": FORMATS[fmt],
            "num_images": count,
        }
        try:
            resp = self._http.post(
                f"{FAL_BASE}/{self.model}",
                json=payload,
                headers={"Authorization": f"Key {self.key}",
                         "Content-Type": "application/json"},
            )
        except httpx.RequestError as exc:
            raise CreativeError(f"Could not reach fal.ai: {exc}")

        if resp.status_code != 200:
            # Surface fal's own reason — a 403 is usually an exhausted balance,
            # not a bad key, and a generic "check your key" message sends people
            # hunting in the wrong place.
            detail = ""
            try:
                detail = (resp.json() or {}).get("detail") or ""
            except ValueError:
                detail = resp.text[:200]
            if isinstance(detail, list):  # 422 validation errors come back as a list
                detail = "; ".join(str(d.get("msg", d)) for d in detail)[:250]
            raise CreativeError(f"fal.ai {resp.status_code}: {detail or resp.text[:200]}")

        body = resp.json() or {}
        images = [
            {"url": im.get("url"), "width": im.get("width"), "height": im.get("height")}
            for im in (body.get("images") or []) if im.get("url")
        ]
        if not images:
            raise CreativeError("fal.ai returned no images.")
        return {"format": fmt, "brief": brief, "images": images,
                "model": self.model, "seed": body.get("seed")}

    def close(self) -> None:
        if self._http is not None:
            self._http.close()

    def __enter__(self) -> "CreativeClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def _mock_generate(brief: str, fmt: str, count: int) -> dict:
    """Deterministic placeholder images for demo/mock modes (no key, no cost)."""
    label = (brief or "concept")[:40].replace(" ", "+")
    size = {"ad_square": "800x800", "ad_story": "720x1280",
            "ad_landscape": "1024x768", "landing_hero": "1280x720"}[fmt]
    return {
        "format": fmt,
        "brief": brief,
        "images": [{"url": f"https://placehold.co/{size}/18191a/8a8f98/png?text={label}",
                    "width": int(size.split("x")[0]), "height": int(size.split("x")[1])}
                   for _ in range(count)],
        "model": "mock",
        "note": "sample placeholder (demo mode)",
    }
