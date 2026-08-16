"""Reader for the user's Reddit problem-mining Airtable base.

The user runs a separate Reddit-scraping pipeline (Make.com -> Airtable) that
collects buyer complaints, workarounds and problem statements. This client
makes that corpus a first-class evidence channel for SaaS-idea validation:
real buyer language, straight from the mining base.

Config (env / .env):
    AIRTABLE_PAT        Personal Access Token (scopes: data.records:read, and
                        schema.bases:read if AIRTABLE_TABLE is left unset)
    AIRTABLE_BASE_ID    app... id of the mining base
    AIRTABLE_TABLE      table name or tbl... id (optional — auto-discovers the
                        likeliest table via the meta API when unset)

Field names are NOT assumed: rows are mapped heuristically (problem/pain/
quote/title/body -> text; subreddit/source/url -> provenance), so the client
works against whatever schema the Make scenario writes.
"""

from __future__ import annotations

import os

import httpx

API = "https://api.airtable.com/v0"

# Heuristic field buckets, matched case-insensitively as substrings.
_TEXT_HINTS = ("problem", "pain", "quote", "statement", "complaint", "title",
               "body", "text", "summary", "post")
_SOURCE_HINTS = ("subreddit", "source", "url", "link", "permalink", "thread")
_META_HINTS = ("niche", "keyword", "topic", "category", "score", "upvote",
               "frequency", "date", "created")


class AirtableError(RuntimeError):
    """Raised for non-retryable Airtable errors."""


class MinedProblemsClient:
    def __init__(self, settings, *, mock: bool = False, timeout: float = 20.0) -> None:
        self.mock = mock
        self.pat = (getattr(settings, "airtable_pat", None)
                    or os.getenv("AIRTABLE_PAT") or os.getenv("AIRTABLE_API_KEY"))
        self.base_id = getattr(settings, "airtable_base_id", None) or os.getenv("AIRTABLE_BASE_ID")
        self.table = getattr(settings, "airtable_table", None) or os.getenv("AIRTABLE_TABLE")
        self._http = None if mock else httpx.Client(
            timeout=timeout,
            headers={"Authorization": f"Bearer {self.pat}"} if self.pat else {})

    # -- internals ---------------------------------------------------------

    def _discover_table(self) -> str:
        r = self._http.get(f"{API}/meta/bases/{self.base_id}/tables")
        if r.status_code != 200:
            raise AirtableError(
                f"Airtable meta {r.status_code}: {r.text[:150]} — set AIRTABLE_TABLE "
                "explicitly, or add the schema.bases:read scope to the PAT.")
        tables = (r.json() or {}).get("tables", [])
        if not tables:
            raise AirtableError("The Airtable base has no tables.")
        for t in tables:  # prefer a table that sounds like the mining output
            name = (t.get("name") or "").lower()
            if any(h in name for h in ("problem", "reddit", "pain", "mining", "post")):
                return t["id"]
        return tables[0]["id"]

    @staticmethod
    def _map_row(fields: dict) -> dict:
        text_parts, source, meta = [], None, {}
        for key, value in fields.items():
            if value in (None, "", [], {}):
                continue
            low = key.lower()
            sval = ", ".join(map(str, value)) if isinstance(value, list) else str(value)
            if any(h in low for h in _TEXT_HINTS):
                text_parts.append(sval)
            elif any(h in low for h in _SOURCE_HINTS):
                source = source or sval[:120]
            elif any(h in low for h in _META_HINTS):
                meta[key] = sval[:60]
        if not text_parts:  # fall back to the longest string field
            strings = [str(v) for v in fields.values() if isinstance(v, str)]
            if strings:
                text_parts = [max(strings, key=len)]
        return {"text": " — ".join(text_parts)[:400] or None,
                "source": source, **({"meta": meta} if meta else {})}

    # -- public API --------------------------------------------------------

    def fetch(self, query: str = "", *, limit: int = 15) -> dict:
        """Return mined problem rows, filtered by `query` terms when given."""
        limit = max(1, min(int(limit or 15), 30))
        if self.mock:
            return _mock_fetch(query, limit)
        if not (self.pat and self.base_id):
            raise AirtableError(
                "The Reddit mining base is not configured. Set AIRTABLE_PAT and "
                "AIRTABLE_BASE_ID (and optionally AIRTABLE_TABLE).")

        table = self.table or self._discover_table()
        rows, offset = [], None
        for _ in range(3):  # up to 300 records scanned
            params = {"pageSize": 100}
            if offset:
                params["offset"] = offset
            r = self._http.get(f"{API}/{self.base_id}/{table}", params=params)
            if r.status_code in (401, 403):
                raise AirtableError(
                    f"Airtable {r.status_code} — check AIRTABLE_PAT (needs "
                    "data.records:read scope and access to this base).")
            if r.status_code == 404:
                raise AirtableError(
                    f"Airtable 404 — base '{self.base_id}' or table '{table}' not "
                    "found. Check AIRTABLE_BASE_ID / AIRTABLE_TABLE.")
            if r.status_code != 200:
                raise AirtableError(f"Airtable {r.status_code}: {r.text[:150]}")
            data = r.json() or {}
            rows.extend(self._map_row(rec.get("fields", {}))
                        for rec in data.get("records", []))
            offset = data.get("offset")
            if not offset:
                break

        rows = [x for x in rows if x.get("text")]
        terms = [t for t in query.lower().split() if len(t) > 2]
        if terms:
            scored = []
            for x in rows:
                blob = (x["text"] + " " + str(x.get("meta", ""))).lower()
                score = sum(1 for t in terms if t in blob)
                if score:
                    scored.append((score, x))
            scored.sort(key=lambda p: -p[0])
            matched = [x for _, x in scored]
            # Fall back to recent rows if the niche filter matches nothing —
            # absence of matches is itself worth reporting, not an error.
            result = matched[:limit]
            return {"query": query, "matched": len(matched),
                    "scanned": len(rows), "results": result or rows[:5],
                    **({} if matched else {"note": "no rows matched the query; "
                                                    "showing recent rows instead"})}
        return {"query": query, "matched": len(rows), "scanned": len(rows),
                "results": rows[:limit]}

    def close(self) -> None:
        if self._http is not None:
            self._http.close()

    def __enter__(self) -> "MinedProblemsClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def _mock_fetch(query: str, limit: int) -> dict:
    q = query or "the workflow"
    rows = [
        {"text": f"I spend 3+ hours every week doing {q} by hand in spreadsheets and "
                 "still catch errors after sending. There has to be a better way.",
         "source": "r/smallbusiness", "meta": {"upvotes": "214"}},
        {"text": f"Tried two tools for {q} — both are $99/mo suites where I use one "
                 "feature. Cancelled both and went back to my template doc.",
         "source": "r/Entrepreneur", "meta": {"upvotes": "87"}},
        {"text": f"Every month-end, {q} eats a full day. My workaround is a chain of "
                 "Zapier + Sheets that breaks whenever a column changes.",
         "source": "r/productivity", "meta": {"upvotes": "45"}},
    ]
    return {"query": query, "matched": len(rows), "scanned": 120,
            "results": rows[:limit], "note": "sample data (demo mode)"}
