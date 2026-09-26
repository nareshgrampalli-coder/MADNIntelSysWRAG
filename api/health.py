"""Vercel-compatible health endpoint."""

import json
from http.server import BaseHTTPRequestHandler
import os

from news_rag import __version__


class handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        payload = json.dumps(
            {
                "status": "ok",
                "service": "news-rag-api",
                "version": __version__,
                "environment": os.getenv("NEWS_RAG_ENV", "production"),
                "vector_backend": os.getenv("NEWS_RAG_VECTOR_BACKEND", "json"),
            }
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.end_headers()
