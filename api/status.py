"""Vercel serverless function: GET /api/status."""

import json
import os
import sys

# Make the repo root importable so `adscout` resolves inside the lambda.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from http.server import BaseHTTPRequestHandler

from adscout.web import status


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps(status()).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
