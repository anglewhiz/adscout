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
               "body", "text", "summary", "post", "content", "selftext")
_SOURCE_HINTS = ("subreddit", "source", "url", "link", "permalink", "thread")
_BUCKET_HINTS = ("bucket", "category", "type", "evidence")


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
            if any(h in low for h in _BUCKET_HINTS) and _normalise_bucket(value):
                bucket = _normalise_bucket(value)
            elif any(h in low for h in _TEXT_HINTS):
                text_parts.append(str(value))
            elif any(h in low for h in _SOURCE_HINTS):
                source = source or str(value)[:120]
            elif len(str(value)) < 60:
                meta[key] = str(value)
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

    def close(self) -> None:
        if self._http is not None:
            self._http.close()

    def __enter__(self) -> "SheetsMinedClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
