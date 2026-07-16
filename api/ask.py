"""Vercel serverless function: POST /api/ask."""

import json
import os
import sys

# Make the repo root importable so `adscout` resolves inside the lambda.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from http.server import BaseHTTPRequestHandler

from adscout.web import AuthError, parse_ask_payload, run_analysis


class handler(BaseHTTPRequestHandler):
    def _json(self, obj, code=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            self._json({"error": "invalid JSON body"}, 400)
            return

        try:
            args = parse_ask_payload(payload)
        except ValueError as exc:
            self._json({"error": str(exc)}, 400)
            return

        try:
            self._json(run_analysis(
                args["question"], mode=args["mode"], country=args["country"],
                max_steps=args["max_steps"], password=args["password"]))
        except AuthError as exc:
            self._json({"error": str(exc), "auth_required": True}, 401)
        except Exception as exc:  # surface a readable message to the UI
            self._json({"error": str(exc)}, 500)
