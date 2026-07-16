"""Configuration loaded from environment variables (or a .env file)."""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass


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
        )

    def has_provider_auth(self) -> bool:
        """True if we can build an Authorization header (either credential form)."""
        return bool(self.spyfu_basic_auth or (self.spyfu_api_id and self.spyfu_secret_key))

    def basic_auth_token(self) -> str:
        """The Base64 token for the 'Authorization: Basic <token>' header.

        Prefers SPYFU_BASIC_AUTH (the pre-generated Base64 SpyFu shows on the
        API Usage page) — copying that verbatim avoids mis-typing the separate
        id/secret. Falls back to Base64-encoding 'SPYFU_API_ID:SECRET_KEY'.
        """
        if self.spyfu_basic_auth:
            return self.spyfu_basic_auth
        if not (self.spyfu_api_id and self.spyfu_secret_key):
            raise RuntimeError(
                "Missing SpyFu credentials. Set SPYFU_BASIC_AUTH (the pre-generated "
                "Base64 from Account Settings > API Usage on spyfu.com), or set "
                "SPYFU_API_ID and SPYFU_SECRET_KEY."
            )
        raw = f"{self.spyfu_api_id}:{self.spyfu_secret_key}".encode()
        return base64.b64encode(raw).decode()
