"""Shared HTTP helpers for the API layer."""

from __future__ import annotations

import base64
import email.utils
import http
import json
import uuid
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from websockets.datastructures import Headers
from websockets.http11 import Response


def http_json_response(data: dict[str, Any], *, status: int = 200) -> Response:
    """Return a JSON HTTP response."""
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    headers = Headers(
        [
            ("Date", email.utils.formatdate(usegmt=True)),
            ("Connection", "close"),
            ("Content-Length", str(len(body))),
            ("Content-Type", "application/json; charset=utf-8"),
        ]
    )
    reason = http.HTTPStatus(status).phrase
    return Response(status, reason, headers, body)


def http_response(
    body: bytes,
    *,
    status: int = 200,
    content_type: str = "text/plain; charset=utf-8",
    extra_headers: list[tuple[str, str]] | None = None,
) -> Response:
    """Return a raw HTTP response."""
    headers = [
        ("Date", email.utils.formatdate(usegmt=True)),
        ("Connection", "close"),
        ("Content-Length", str(len(body))),
        ("Content-Type", content_type),
    ]
    if extra_headers:
        headers.extend(extra_headers)
    reason = http.HTTPStatus(status).phrase
    return Response(status, reason, Headers(headers), body)


def http_error(status: int, message: str | None = None) -> Response:
    """Return an HTTP error response."""
    body = (message or http.HTTPStatus(status).phrase).encode("utf-8")
    return http_response(body, status=status)


def parse_query(path_with_query: str) -> dict[str, list[str]]:
    """Extract query parameters from a path."""
    parsed = urlparse("http://x" + path_with_query)
    return parse_qs(parsed.query)


def query_first(query: dict[str, list[str]], key: str) -> str | None:
    """Return the first value for *key*, or None."""
    values = query.get(key)
    return values[0] if values else None


def parse_mutation_data(query: dict[str, list[str]]) -> dict[str, Any] | Response:
    """Parse and validate the `data` query parameter as JSON.

    Returns the parsed dict on success, or an HTTP error Response on failure.
    """
    raw = query_first(query, "data")
    if not raw:
        return http_error(400, "missing data parameter")
    try:
        payload = json.loads(unquote(raw))
    except (json.JSONDecodeError, TypeError):
        return http_error(400, "invalid JSON in data parameter")
    if not isinstance(payload, dict):
        return http_error(400, "data must be a JSON object")
    return payload


def generate_id() -> str:
    """Generate a short unique ID."""
    return uuid.uuid4().hex[:12]


def normalize_path(path_with_query: str) -> str:
    """Return the path component with trailing slash stripped (root stays ``/``)."""
    parsed = urlparse("http://x" + path_with_query)
    path = parsed.path or "/"
    if len(path) > 1 and path.endswith("/"):
        return path.rstrip("/")
    return path


def bearer_token(headers: Any) -> str | None:
    """Pull a Bearer token out of standard or query-style headers."""
    auth = headers.get("Authorization") or headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth[7:].strip() or None
    return None


def b64url_encode(data: bytes) -> str:
    """URL-safe base64 without padding — compact + friendly in URL paths."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64url_decode(s: str) -> bytes:
    """Reverse of :func:`b64url_encode`; caller handles ``ValueError``."""
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)
