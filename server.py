"""Local dev server for the AdScout web UI.

Serves the static frontend and a small JSON API so you can ask marketing
questions from the browser. It mirrors the Vercel serverless functions in
``api/`` — both import the same logic from ``adscout.web`` — so what you see
locally is what you get in production.

    python server.py                 # then open http://localhost:8000

Zero extra dependencies: Python standard library plus the ``adscout`` package.
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from adscout.web import (AuthError, check_diagnostic_access, parse_ask_payload,
                         ping_provider, run_analysis, status)

HERE = Path(__file__).resolve().parent
INDEX_HTML = HERE / "public" / "index.html"


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send_json(self, obj: dict, code: int = 200) -> None:
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: bytes) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.end_headers()
        self.wfile.write(html)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path in ("/", "/index.html"):
            # Local dev: serve the file directly. On Vercel the static file is
            # NOT on the function's disk (public/ is served by the static CDN),
            # so bounce "/" to the statically-served /index.html.
            if INDEX_HTML.exists():
                self._send_html(INDEX_HTML.read_bytes())
            elif path == "/":
                self.send_response(308)
                self.send_header("Location", "/index.html")
                self.send_header("Content-Length", "0")
                self.end_headers()
            else:
                self._send_json({"error": "UI not found"}, 404)
            return
        if path == "/api/status":
            self._send_json(status())
            return
        if path == "/api/ping-provider":
            pw = (parse_qs(parsed.query).get("password") or [""])[0]
            try:
                check_diagnostic_access(pw)
            except AuthError as exc:
                self._send_json({"error": str(exc), "auth_required": True}, 401)
                return
            self._send_json(ping_provider())
            return
        self._send_json({"error": "not found"}, 404)

    def do_POST(self) -> None:
        if self.path != "/api/ask":
            self._send_json({"error": "not found"}, 404)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            self._send_json({"error": "invalid JSON body"}, 400)
            return

        try:
            args = parse_ask_payload(payload)
        except ValueError as exc:
            self._send_json({"error": str(exc)}, 400)
            return

        try:
            self._send_json(run_analysis(
                args["question"], mode=args["mode"], country=args["country"],
                max_steps=args["max_steps"], password=args["password"]))
        except AuthError as exc:
            self._send_json({"error": str(exc), "auth_required": True}, 401)
        except Exception as exc:  # surface a readable message to the UI
            self._send_json({"error": str(exc)}, 500)

    def log_message(self, fmt: str, *args) -> None:
        print(f"  {self.address_string()} - {fmt % args}")


def main() -> None:
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "127.0.0.1")
    server = ThreadingHTTPServer((host, port), Handler)
    st = status()
    print("AdScout — web UI")
    print(f"  serving on http://{host}:{port}")
    print(f"  ANTHROPIC_API_KEY: {'set' if st['has_anthropic'] else 'MISSING'}   "
          f"provider creds: {'set' if st['has_provider'] else 'MISSING'}")
    if not st["has_anthropic"]:
        print("  tip: no keys? Use Demo mode in the UI — it runs fully offline.")
    print("  press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down")
        server.shutdown()


if __name__ == "__main__":
    main()
