"""Shared web logic for AdScout's browser frontend.

This module is transport-agnostic: it exposes ``run_analysis`` and ``status``
plus a keyless "demo" reasoner. It is imported by both the local dev server
(``server.py``) and the Vercel serverless functions under ``api/``.

Modes:
    live   real data-provider API + real Claude   (needs provider creds + ANTHROPIC_API_KEY)
    mock   fake data + real Claude                 (needs only ANTHROPIC_API_KEY)
    demo   fake data + scripted Claude             (needs no keys at all — fully offline)
"""

from __future__ import annotations

import hmac
import os
import re
from types import SimpleNamespace

from .analyst import Analyst
from .client import SpyFuClient
from .config import Settings
from .endpoints import COUNTRY_CODES

# Values from .env.example that mean "not actually filled in yet".
_PLACEHOLDERS = {"", "your_secret_key", "00000000-0000-0000-0000-000000000000"}


def _real(value: str | None) -> bool:
    """True only for a credential that looks genuinely set (not a placeholder)."""
    return bool(value) and value not in _PLACEHOLDERS and "..." not in value


def _provider_ready(settings) -> bool:
    """True if provider auth is usable: a real Base64 token, or real id+secret."""
    if _real(settings.spyfu_basic_auth):
        return True
    return _real(settings.spyfu_api_id) and _real(settings.spyfu_secret_key)


class AuthError(RuntimeError):
    """Raised when a password-protected mode is requested without a valid password."""


def _access_password() -> str:
    """The shared password gating the paid (mock/live) modes, if configured.

    Set ACCESS_PASSWORD (or ADSCOUT_PASSWORD) in the environment / Vercel to
    require a password for Mock and Live. Leave it unset to keep those modes
    open (typical for local development). Demo is never gated.
    """
    return (os.getenv("ACCESS_PASSWORD") or os.getenv("ADSCOUT_PASSWORD") or "").strip()


def _check_access(mode: str, password: str) -> None:
    """Enforce the password gate for paid modes. Raises AuthError if it fails."""
    if mode == "demo":
        return
    expected = _access_password()
    if not expected:
        return  # no gate configured
    if not hmac.compare_digest((password or "").strip(), expected):
        raise AuthError(
            "This mode is password-protected. Enter the access password to run "
            "Mock or Live analyses. (Demo mode is always open.)"
        )

# --------------------------------------------------------------------------
# Demo mode: a scripted "Claude" that needs no API key.
# --------------------------------------------------------------------------
# It mirrors the shape of the real reasoning loop (a few tool_use turns, then a
# final verdict) so the whole UI — including the evidence trace — can be
# explored offline. Numbers below match the deterministic mock data payloads.

_FILLER = {
    "how", "are", "people", "running", "ads", "ad", "in", "the", "on", "who",
    "advertises", "advertise", "advertising", "what", "is", "anyone", "spending",
    "big", "niche", "space", "do", "does", "they", "use", "and", "for", "a", "an",
    "of", "to", "with", "market", "someone", "much", "money", "which", "brands",
    "companies", "run", "against",
}


def _topic_from_question(question: str) -> str:
    """Best-effort extraction of a seed topic for the demo's mock lookups."""
    quoted = re.findall(r"['\"]([^'\"]+)['\"]", question)
    if quoted:
        return quoted[0].strip()
    words = [w for w in re.findall(r"[a-zA-Z][a-zA-Z-]*", question.lower())
             if w not in _FILLER]
    topic = " ".join(words[:3]).strip()
    return topic or "dog food"


class _DemoAnthropic:
    """Scripts a realistic multi-step analysis without any network or API key."""

    def __init__(self, topic: str) -> None:
        self.topic = topic
        self.calls = 0
        self.messages = self  # Analyst calls self.ai.messages.create(...)

    def create(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            return self._tool("find_advertisers_for_topic",
                              {"topic": self.topic, "limit": 5})
        if self.calls == 2:
            return self._tool("get_keyword_ad_history",
                              {"keyword": f"best {self.topic}", "limit": 5})
        if self.calls == 3:
            return self._tool("get_domain_stats", {"domain": "chewy.com"})
        return self._final()

    @staticmethod
    def _tool(name: str, tool_input: dict):
        block = SimpleNamespace(type="tool_use", id=f"demo_{name}",
                                name=name, input=tool_input)
        return SimpleNamespace(stop_reason="tool_use", content=[block])

    def _final(self):
        t = self.topic
        text = (
            f"The {t} PPC space is actively and heavily advertised, dominated by a "
            f"few well-funded advertisers.\n\n"
            f"chewy.com runs the widest coverage (est. $812K/mo ad budget, 5,871 "
            f"paid keywords, avg ad rank 1.4), leaning on \"free 1-2 day shipping\" "
            f"and \"autoship & save 35%\" offers. Challenger brands like "
            f"thefarmersdog.com compete on a \"fresh, human-grade\" angle with an "
            f"aggressive 50%-off trial.\n\n"
            f"Top keywords by volume: \"best {t}\" (74K searches, ~$1.42 CPC, 18 "
            f"advertisers), \"grain free {t}\" (33K, ~$2.05 CPC), \"{t} delivery\" "
            f"(12K, ~$3.10 CPC).\n\n"
            f"VERDICT: SUPPORTED — the niche is actively and heavily advertised.\n"
            f"Key numbers: 18 distinct advertisers on \"best {t}\"; top CPC ~$3.10 "
            f"on \"{t} delivery\"; chewy.com est. $812K/mo budget at avg ad rank 1.4.\n\n"
            f"(Demo mode — figures are from offline sample data, not a live API.)"
        )
        block = SimpleNamespace(type="text", text=text)
        return SimpleNamespace(stop_reason="end_turn", content=[block])


# --------------------------------------------------------------------------
# Public entry points used by the HTTP layers.
# --------------------------------------------------------------------------

def run_analysis(question: str, *, mode: str, country: str, max_steps: int,
                 password: str = "") -> dict:
    """Run one analysis and return a JSON-serializable result dict."""
    _check_access(mode, password)

    settings = Settings.load()
    if country:
        settings.default_country = country

    if mode == "demo":
        anthropic_client = _DemoAnthropic(_topic_from_question(question))
        data_mock = True
    elif mode == "mock":
        if not _real(settings.anthropic_api_key):
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Mock mode still uses real Claude "
                "reasoning (only the data is faked). Set the key, or switch to "
                "Demo mode which needs no keys."
            )
        anthropic_client = None
        data_mock = True
    else:  # live
        if not _real(settings.anthropic_api_key):
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Set it, or use Demo mode which "
                "needs no keys."
            )
        if not _provider_ready(settings):
            raise RuntimeError(
                "Data-provider credentials are not set. Use Mock mode to test the "
                "pipeline with sample data, or Demo mode which needs no keys."
            )
        anthropic_client = None
        data_mock = False

    with SpyFuClient(settings, mock=data_mock) as client:
        analyst = Analyst(
            client,
            anthropic_client=anthropic_client,
            model=settings.model,
            default_country=settings.default_country,
            max_steps=max_steps,
        )
        result = analyst.ask(question)

    return {
        "answer": result.answer,
        "steps": result.steps,
        "mode": mode,
        "trace": [
            {"name": c.name, "input": c.input, "result_summary": c.result_summary}
            for c in result.trace
        ],
    }


def ping_provider() -> dict:
    """Diagnose the data-provider (SpyFu) connection without exposing secrets.

    Reports credential *shape* (lengths, present/placeholder, UUID-ish id) and
    makes ONE real, cheap call to surface the provider's actual response — so a
    401 vs 200 is unambiguous. No secret values are ever returned.
    """
    settings = Settings.load()
    aid = settings.spyfu_api_id or ""
    sec = settings.spyfu_secret_key or ""
    basic = settings.spyfu_basic_auth or ""
    info = {
        "auth_mode": settings.auth_mode(),
        "basic_auth_present": _real(basic),
        "basic_auth_len": len(basic),
        "api_id_present": _real(aid),
        "secret_present": _real(sec),
        "api_id_len": len(aid),
        "secret_len": len(sec),
        "api_id_looks_like_uuid": bool(re.fullmatch(r"[0-9a-fA-F-]{32,40}", aid.strip())),
        "api_id_has_whitespace": aid != aid.strip(),
        "secret_has_whitespace": sec != sec.strip(),
    }
    if not _provider_ready(settings):
        info["ok"] = False
        info["result"] = "Credentials are not set (empty or still the placeholder)."
        return info
    try:
        with SpyFuClient(settings, mock=False) as c:
            data = c.call("latest_domain_stats", domain="ebay.com", countryCode="US")
        info["ok"] = True
        info["result"] = f"OK — SpyFu accepted the credentials ({len(data.get('results') or [])} row(s))."
    except Exception as exc:
        info["ok"] = False
        info["result"] = f"FAILED — {exc}"
    return info


def status() -> dict:
    """Report which credentials are configured (drives UI mode availability)."""
    settings = Settings.load()
    return {
        "has_anthropic": _real(settings.anthropic_api_key),
        "has_provider": _provider_ready(settings),
        "auth_required": bool(_access_password()),
        "model": settings.model,
        "default_country": settings.default_country,
        "countries": COUNTRY_CODES,
    }


def parse_ask_payload(payload: dict) -> dict:
    """Validate/normalize an incoming /api/ask body. Raises ValueError if bad."""
    question = (payload.get("question") or "").strip()
    if not question:
        raise ValueError("Please enter a question.")
    mode = payload.get("mode", "demo")
    if mode not in ("live", "mock", "demo"):
        mode = "demo"
    country = (payload.get("country") or "").strip().upper()
    try:
        max_steps = max(1, min(12, int(payload.get("max_steps", 8))))
    except (TypeError, ValueError):
        max_steps = 8
    password = str(payload.get("password") or "")
    return {"question": question, "mode": mode, "country": country,
            "max_steps": max_steps, "password": password}
