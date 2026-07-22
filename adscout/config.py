"""Configuration loaded from environment variables (or a .env file)."""

from __future__ import annotations

import base64
import os
import re
from dataclasses import dataclass

_UUID_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
                      r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")


def _looks_like_basic_token(value: str, api_id: str | None) -> bool:
    """True if `value` is a pre-generated Base64 of '<id>:<secret>'.

    Detects the common mix-up of pasting SpyFu's ready-made Base64 string into
    the secret field. Requires the decoded left-hand side (before the colon) to
    be the configured api_id or a UUID, so a genuine secret is not misread.
    """
    v = (value or "").strip()
    if len(v) < 24 or len(v) % 4 != 0:
        return False
    try:
        decoded = base64.b64decode(v, validate=True).decode("utf-8", "strict")
    except Exception:
        return False
    if ":" not in decoded:
        return False
    left = decoded.split(":", 1)[0]
    if api_id and left == api_id.strip():
        return True
    return bool(_UUID_RE.fullmatch(left))


def _load_dotenv() -> None:
    """Minimal .env loader (no dependency). Only sets vars not already present."""
    path = os.path.join(os.getcwd(), ".env")
    if not os.path.exists(path):
        return
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


@dataclass
class Settings:
    spyfu_api_id: str | None
    spyfu_secret_key: str | None
    anthropic_api_key: str | None
    model: str
    default_country: str
    # Optional pre-generated Base64 of "id:secret" (SpyFu API Usage page).
    spyfu_basic_auth: str | None = None
    # Apify token for the Meta (Facebook/Instagram) Ad Library scraper.
    apify_token: str | None = None
    # Moz Links API credentials (SEO authority / backlinks).
    moz_access_id: str | None = None
    moz_secret_key: str | None = None
    # Hexomatic key — landing-page screenshot capture.
    hexomatic_api_key: str | None = None

    @classmethod
    def load(cls) -> "Settings":
        _load_dotenv()
        basic = (os.getenv("SPYFU_BASIC_AUTH") or os.getenv("SPYFU_API_BASE64") or "").strip()
        # Tolerate the value being pasted with a leading "Basic " prefix.
        if basic.lower().startswith("basic "):
            basic = basic[6:].strip()
        return cls(
            spyfu_api_id=os.getenv("SPYFU_API_ID"),
            spyfu_secret_key=os.getenv("SPYFU_SECRET_KEY") or os.getenv("SPYFU_API_KEY"),
            spyfu_basic_auth=basic or None,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            # Any current Claude model works; override with ANALYST_MODEL.
            model=os.getenv("ANALYST_MODEL", "claude-sonnet-5"),
            default_country=os.getenv("SPYFU_COUNTRY", "US"),
            apify_token=os.getenv("APIFY_TOKEN"),
            moz_access_id=os.getenv("MOZ_ACCESS_ID"),
            moz_secret_key=os.getenv("MOZ_SECRET_KEY"),
            hexomatic_api_key=os.getenv("HEXOMATIC_API_KEY"),
        )

    def has_provider_auth(self) -> bool:
        """True if we can build an Authorization header (either credential form)."""
        return bool(self.spyfu_basic_auth or (self.spyfu_api_id and self.spyfu_secret_key))

    def basic_auth_token(self) -> str:
        """The Base64 token for the 'Authorization: Basic <token>' header.

        Prefers SPYFU_BASIC_AUTH (the pre-generated Base64 SpyFu shows on the
        API Usage page). Otherwise Base64-encodes 'SPYFU_API_ID:SECRET_KEY' —
        but if the "secret" is itself that pre-generated Base64 token (a common
        mix-up), it is used verbatim instead of being double-encoded.
        """
        if self.spyfu_basic_auth:
            return self.spyfu_basic_auth
        if self.spyfu_secret_key and _looks_like_basic_token(self.spyfu_secret_key,
                                                              self.spyfu_api_id):
            return self.spyfu_secret_key.strip()
        if not (self.spyfu_api_id and self.spyfu_secret_key):
            raise RuntimeError(
                "Missing SpyFu credentials. Set SPYFU_BASIC_AUTH (the pre-generated "
                "Base64 from Account Settings > API Usage on spyfu.com), or set "
                "SPYFU_API_ID and SPYFU_SECRET_KEY."
            )
        raw = f"{self.spyfu_api_id}:{self.spyfu_secret_key}".encode()
        return base64.b64encode(raw).decode()

    def auth_mode(self) -> str:
        """Which credential form will be used (for diagnostics)."""
        if self.spyfu_basic_auth:
            return "base64"
        if self.spyfu_secret_key and _looks_like_basic_token(self.spyfu_secret_key,
                                                             self.spyfu_api_id):
            return "base64-in-secret"
        return "id+secret"
