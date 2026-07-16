"""Offline tests — no network, no credentials required.

Run with:  python -m pytest -q   (or)   python tests/test_offline.py
"""

from __future__ import annotations

import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adscout.analyst import Analyst
from adscout.client import SpyFuClient, SpyFuError
from adscout.config import Settings
from adscout.endpoints import ENDPOINTS


def _settings() -> Settings:
    return Settings(spyfu_api_id="id", spyfu_secret_key="key",
                    anthropic_api_key=None, model="test-model", default_country="US")


# --- endpoint registry / URL construction --------------------------------

def test_endpoint_urls_are_absolute_and_versioned():
    for ep in ENDPOINTS.values():
        url = ep.url()
        assert url.startswith("https://api.spyfu.com/apis/")
        assert "/v2/" in url
    # spot-check the non-guessable server segment
    assert ENDPOINTS["term_ad_history"].url() == (
        "https://api.spyfu.com/apis/cloud_ad_history_api/v2/term/getTermAdHistory"
    )


def test_client_mock_returns_shaped_data():
    with SpyFuClient(_settings(), mock=True) as c:
        data = c.call("keyword_expansions", query="dog food",
                      keywordSearchType="AlsoBuysAdsFor")
        assert data["results"][0]["distinctCompetitors"]  # advertiser list present


def test_missing_required_param_raises():
    with SpyFuClient(_settings(), mock=True) as c:
        try:
            c.call("term_ad_history")  # missing 'term'
        except SpyFuError as exc:
            assert "term" in str(exc)
        else:
            raise AssertionError("expected SpyFuError")


def test_none_params_are_dropped_in_mock():
    with SpyFuClient(_settings(), mock=True) as c:
        # pastNMonths=None should be dropped, not passed through
        data = c.call("latest_domain_stats", domain="chewy.com", pastNMonths=None)
        assert data["results"][0]["monthlyBudget"] > 0


# --- full orchestration loop with a scripted fake Claude -----------------

class _FakeAnthropic:
    """Scripts a two-turn conversation: one tool_use turn, then a final answer."""

    def __init__(self):
        self.calls = 0
        self.messages = self

    def create(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            block = SimpleNamespace(
                type="tool_use", id="tu_1",
                name="find_advertisers_for_topic",
                input={"topic": "dog food", "limit": 5},
            )
            return SimpleNamespace(stop_reason="tool_use", content=[block])
        # second call: model has the tool_result, produces final text
        text = SimpleNamespace(type="text",
                               text="Top advertisers include chewy.com. VERDICT: SUPPORTED.")
        return SimpleNamespace(stop_reason="end_turn", content=[text])


def test_orchestration_dispatches_tool_and_returns_answer():
    with SpyFuClient(_settings(), mock=True) as spyfu:
        analyst = Analyst(spyfu, anthropic_client=_FakeAnthropic(), model="test-model")
        result = analyst.ask("How are people running ads in the dog food niche?")

    assert "SUPPORTED" in result.answer
    assert result.steps == 2
    assert len(result.trace) == 1
    assert result.trace[0].name == "find_advertisers_for_topic"
    assert "rows" in result.trace[0].result_summary


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"\nAll {len(fns)} tests passed.")
