"""Reader for the user's Reddit problem-mining Google Sheet.

The user's Make.com scraper writes mined Reddit posts to a Google Sheet. For a
sheet shared as "anyone with the link can view", Google serves it as CSV with
NO credentials at all via the gviz endpoint — so the only config is the
spreadsheet ID (and optionally a tab name):

    GSHEET_ID    the long id between /d/ and /edit in the sheet's URL
    GSHEET_TAB   optional tab name (defaults to the first tab)

Rows are mapped heuristically like the Airtable reader, with one upgrade: the
user's config uses evidence buckets (A_pain_mining / B_buyer_intent /
C_transition_fear / D_comparison), so a bucket-ish column is preserved and
normalised — the validator routes each row to the right evidence section.
"""

from __future__ import annotations

import csv
import io
import os

import httpx

from .airtable_client import _mock_fetch, _normalise_bucket  # shared corpus shape

_TEXT_HINTS = ("problem", "pain", "quote", "statement", "complaint", "title",
               "body", "text", "summary", "post", "selftext")
_SOURCE_HINTS = ("subreddit", "source", "url", "link", "permalink", "thread",
                 "community")
_BUCKET_HINTS = ("bucket", "category", "type", "evidence")
_META_KEEP = ("upvote", "vote", "comment", "score", "date", "flair", "search")


class SheetsError(RuntimeError):
    """Raised for non-retryable Google Sheets errors."""


def rows_from_csv(text: str) -> list[dict]:
    """Parse the sheet CSV into compact evidence rows (pure, testable)."""
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for rec in reader:
        text_parts, source, bucket, meta = [], None, None, {}
        for key, value in (rec or {}).items():
            if not key or value in (None, ""):
                continue
            low = key.lower()
            sval = str(value)
            if any(h in low for h in _BUCKET_HINTS) and _normalise_bucket(value):
                bucket = _normalise_bucket(value)
            elif any(h in low for h in _SOURCE_HINTS):
                if "id" in low.replace("hidden", ""):  # communityId etc. are not names
                    continue
                # community/subreddit name beats a bare URL for readability
                if source is None or (not sval.startswith("http")
                                      and ("communityname" in low.replace("_", "")
                                           or "subreddit" in low)):
                    source = sval[:120]
            elif any(h in low for h in _TEXT_HINTS) and not sval.startswith("http"):
                text_parts.append(sval)
            elif any(h in low for h in _META_KEEP) and len(sval) < 60:
                meta[key] = sval
        if not text_parts:  # fall back to the longest cell
            strings = [str(v) for v in rec.values() if v]
            if strings:
                text_parts = [max(strings, key=len)]
        row = {"text": " — ".join(text_parts)[:400] or None, "source": source}
        if bucket:
            row["bucket"] = bucket
        if meta:
            row["meta"] = {k: v for k, v in list(meta.items())[:3]}
        rows.append(row)
    return [r for r in rows if r.get("text")]


class SheetsMinedClient:
    def __init__(self, settings, *, mock: bool = False, timeout: float = 20.0) -> None:
        self.mock = mock
        self.sheet_id = getattr(settings, "gsheet_id", None) or os.getenv("GSHEET_ID")
        self.tab = getattr(settings, "gsheet_tab", None) or os.getenv("GSHEET_TAB")
        self._http = None if mock else httpx.Client(timeout=timeout, follow_redirects=True)

    def fetch(self, query: str = "", *, limit: int = 15) -> dict:
        """Return mined problem rows, filtered by `query` terms when given."""
        limit = max(1, min(int(limit or 15), 30))
        if self.mock:
            return _mock_fetch(query, limit)
        if not self.sheet_id:
            raise SheetsError(
                "The Reddit mining sheet is not configured. Set GSHEET_ID (the id "
                "from the sheet's URL) and share the sheet as 'anyone with the "
                "link can view'.")

        url = (f"https://docs.google.com/spreadsheets/d/{self.sheet_id}"
               f"/gviz/tq?tqx=out:csv")
        if self.tab:
            url += f"&sheet={httpx.QueryParams({'s': self.tab})['s']}"
        try:
            r = self._http.get(url)
        except httpx.RequestError as exc:
            raise SheetsError(f"Could not reach Google Sheets: {exc}")
        if r.status_code != 200 or "<html" in r.text[:200].lower():
            raise SheetsError(
                f"Google Sheets returned {r.status_code} — check GSHEET_ID and that "
                "the sheet is shared as 'anyone with the link can view'.")

        rows = rows_from_csv(r.text)
        terms = [t for t in query.lower().split() if len(t) > 2]
        if terms:
            scored = []
            for x in rows:
                blob = (x["text"] + " " + str(x.get("meta", "")) + " "
                        + str(x.get("source", ""))).lower()
                score = sum(1 for t in terms if t in blob)
                if score:
                    scored.append((score, x))
            scored.sort(key=lambda p: -p[0])
            matched = [x for _, x in scored]
            return {"query": query, "matched": len(matched), "scanned": len(rows),
                    "results": matched[:limit] or rows[:5],
                    **({} if matched else {"note": "no rows matched the query; "
                                                    "showing recent rows instead"})}
        return {"query": query, "matched": len(rows), "scanned": len(rows),
                "results": rows[:limit]}

    # -- synthesized insights (the pipeline's own analysis tabs) -------------

    def _tab_csv(self, tab: str) -> str:
        url = (f"https://docs.google.com/spreadsheets/d/{self.sheet_id}"
               f"/gviz/tq?tqx=out:csv&sheet={httpx.QueryParams({'s': tab})['s']}")
        r = self._http.get(url)
        if r.status_code != 200 or "<html" in r.text[:200].lower():
            raise SheetsError(f"Could not read tab '{tab}' (HTTP {r.status_code}).")
        return r.text

    def insights(self, query: str = "", *, limit: int = 6) -> dict:
        """Synthesized insight briefs + activation angles from the mining pipeline.

        Reads the analysis tabs the user's Make scenario writes downstream of the
        raw scrape: per-run insight briefs (root causes, failed solutions, belief
        gaps, high-intent signals, opportunity angles) and generated activation
        material (hooks / angles / objections / CTAs per niche).
        """
        limit = max(1, min(int(limit or 6), 10))
        if self.mock:
            return _mock_insights(query, limit)
        if not self.sheet_id:
            raise SheetsError(
                "The mining sheet is not configured. Set GSHEET_ID to enable "
                "insight briefs.")

        insights_tab = os.getenv("GSHEET_INSIGHTS_TAB", "Sheet2")
        activation_tab = os.getenv("GSHEET_ACTIVATION_TAB", "Activation")
        terms = [t for t in query.lower().split() if len(t) > 2]

        def load(tab: str, fields: tuple, meta_fields: tuple) -> list[dict]:
            rows = []
            for rec in csv.DictReader(io.StringIO(self._tab_csv(tab))):
                row = {k: str(v)[:350] for k, v in (rec or {}).items()
                       if k in fields and v not in (None, "")}
                row.update({k: str(v)[:60] for k, v in (rec or {}).items()
                            if k in meta_fields and v not in (None, "")})
                if row:
                    rows.append(row)
            if terms:
                scored = []
                for row in rows:
                    blob = " ".join(map(str, row.values())).lower()
                    score = sum(1 for t in terms if t in blob)
                    if score:
                        scored.append((score, row))
                scored.sort(key=lambda p: -p[0])
                rows = [r for _, r in scored]
            return rows[:limit]

        briefs = load(insights_tab,
                      ("core_problem_statement", "root_causes", "failed_solutions",
                       "successful_solutions", "emotional_drivers", "belief_gaps",
                       "high_intent_signals", "opportunity_angles"),
                      ("pain_type_analyzed", "run_date", "post_count"))
        activation = load(activation_tab,
                          ("hooks", "angles", "objections", "ctas"),
                          ("niche", "pain_type", "run_date"))
        return {"query": query, "insight_briefs": briefs, "activation": activation,
                **({"note": "no briefs matched the query"} if terms and not briefs
                   else {})}

    def close(self) -> None:
        if self._http is not None:
            self._http.close()

    def __enter__(self) -> "SheetsMinedClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def _mock_insights(query: str, limit: int) -> dict:
    q = query or "the niche"
    return {
        "query": query,
        "insight_briefs": [{
            "core_problem_statement": f"Buyers in {q} distrust mainstream options but fear "
                                      "DIY alternatives backfiring.",
            "failed_solutions": "Home remedies from influencer content; cheap generic products.",
            "belief_gaps": "Assumes 'natural' means safe; assumes premium price means efficacy.",
            "high_intent_signals": "Asking for specific brand comparisons and 'is X worth it'.",
            "opportunity_angles": "Evidence-based middle path between mainstream and DIY.",
            "pain_type_analyzed": "trust_conflicts", "post_count": "70",
        }],
        "activation": [{
            "hooks": f"Did my DIY {q} fix just make it worse?",
            "angles": "Science-first without the harsh trade-offs",
            "objections": "Is this just another overpriced 'clean' product?",
            "ctas": "Take the 60-second check", "niche": q,
        }],
        "note": "sample data (demo mode)",
    }
