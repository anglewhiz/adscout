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

    @classmethod
    def load(cls) -> "Settings":
        _load_dotenv()
        return cls(
            spyfu_api_id=os.getenv("SPYFU_API_ID"),
            spyfu_secret_key=os.getenv("SPYFU_SECRET_KEY") or os.getenv("SPYFU_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            # Any current Claude model works; override with ANALYST_MODEL.
            model=os.getenv("ANALYST_MODEL", "claude-sonnet-5"),
            default_country=os.getenv("SPYFU_COUNTRY", "US"),
        )

    def basic_auth_token(self) -> str:
        """Base64 of 'SPYFU_API_ID:SECRET_KEY' for the Authorization: Basic header."""
        if not (self.spyfu_api_id and self.spyfu_secret_key):
            raise RuntimeError(
                "Missing SpyFu credentials. Set SPYFU_API_ID and SPYFU_SECRET_KEY "
                "(find them under Account Settings > API Usage on spyfu.com)."
            )
        raw = f"{self.spyfu_api_id}:{self.spyfu_secret_key}".encode()
        return base64.b64encode(raw).decode()
