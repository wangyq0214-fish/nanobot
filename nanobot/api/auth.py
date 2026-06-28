"""Authentication and user management for the WebSocket channel."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import shutil
import time
from pathlib import Path
from typing import Any

import bcrypt
from loguru import logger
from websockets.http11 import Request as WsRequest
from websockets.http11 import Response

from nanobot.api.utils import (
    bearer_token,
    http_error,
    http_json_response,
    http_response,
    parse_mutation_data,
    parse_query,
    query_first,
)

_MAX_ISSUED_TOKENS = 10_000


def _issue_route_secret_matches(headers: Any, configured_secret: str) -> bool:
    """Return True if the token-issue HTTP request carries credentials matching the secret."""
    if not configured_secret:
        return True
    authorization = headers.get("Authorization") or headers.get("authorization")
    if authorization and authorization.lower().startswith("bearer "):
        supplied = authorization[7:].strip()
        return hmac.compare_digest(supplied, configured_secret)
    header_token = headers.get("X-Nanobot-Auth") or headers.get("x-nanobot-auth")
    if not header_token:
        return False
    return hmac.compare_digest(header_token.strip(), configured_secret)


class AuthManager:
    """Manages tokens, user registration and validation."""

    def __init__(
        self,
        *,
        token: str = "",
        token_issue_secret: str = "",
        token_ttl_s: int = 300,
        websocket_requires_token: bool = True,
        ws_path: str = "/",
    ):
        self._token = token.strip()
        self._token_issue_secret = token_issue_secret.strip()
        self._token_ttl_s = token_ttl_s
        self._websocket_requires_token = websocket_requires_token
        self._ws_path = ws_path

        # Single-use tokens consumed at WebSocket handshake.
        self._issued_tokens: dict[str, float] = {}
        # Multi-use tokens for the embedded webui's REST surface.
        self._api_tokens: dict[str, float] = {}
        # Token metadata: role, user_id associated with each token.
        self._token_metadata: dict[str, dict[str, str]] = {}

    # -- Token management ----------------------------------------------------

    def _purge_expired(self) -> None:
        """Remove expired tokens from both pools and metadata."""
        now = time.monotonic()
        for pool in (self._issued_tokens, self._api_tokens):
            for token_key, expiry in list(pool.items()):
                if now > expiry:
                    pool.pop(token_key, None)
                    self._token_metadata.pop(token_key, None)

    def issue_token(self, *, role: str = "", user_id: str = "") -> str:
        """Issue a new token registered in both pools. Returns the token string."""
        self._purge_expired()
        if (
            len(self._issued_tokens) >= _MAX_ISSUED_TOKENS
            or len(self._api_tokens) >= _MAX_ISSUED_TOKENS
        ):
            raise RuntimeError("too many outstanding tokens")

        token = f"nbwt_{secrets.token_urlsafe(32)}"
        expiry = time.monotonic() + float(self._token_ttl_s)
        self._issued_tokens[token] = expiry
        self._api_tokens[token] = expiry

        if role or user_id:
            self._token_metadata[token] = {"role": role, "user_id": user_id}

        return token

    def issue_separate_tokens(self, *, role: str = "", user_id: str = "") -> dict[str, str]:
        """Issue separate tokens for WebSocket and REST API.

        Returns a dict with:
        - ws_token: Single-use token for WebSocket handshake (consumed on use)
        - api_token: Multi-use token for REST API calls (TTL-bound)
        """
        self._purge_expired()
        if (
            len(self._issued_tokens) >= _MAX_ISSUED_TOKENS
            or len(self._api_tokens) >= _MAX_ISSUED_TOKENS
        ):
            raise RuntimeError("too many outstanding tokens")

        # WS token: single-use, shorter TTL (60 seconds)
        ws_token = f"nbws_{secrets.token_urlsafe(32)}"
        ws_expiry = time.monotonic() + 60.0  # 60 seconds for WS handshake
        self._issued_tokens[ws_token] = ws_expiry

        # API token: multi-use, configurable TTL
        api_token = f"nbapi_{secrets.token_urlsafe(32)}"
        api_expiry = time.monotonic() + float(self._token_ttl_s)
        self._api_tokens[api_token] = api_expiry

        # Store metadata for both tokens
        metadata = {}
        if role:
            metadata["role"] = role
        if user_id:
            metadata["user_id"] = user_id

        if metadata:
            self._token_metadata[ws_token] = metadata.copy()
            self._token_metadata[api_token] = metadata.copy()
            logger.debug("[auth] issue_separate_tokens: stored metadata={}, api_token_prefix={}", metadata, api_token[:20])
        else:
            logger.warning("[auth] issue_separate_tokens: no metadata to store (role={!r}, user_id={!r})", role, user_id)

        return {"ws_token": ws_token, "api_token": api_token}

    def take_issued_token(self, token_value: str | None) -> bool:
        """Validate and consume one issued token (single use)."""
        if not token_value:
            return False
        self._purge_expired()
        expiry = self._issued_tokens.pop(token_value, None)
        if expiry is None:
            return False
        if time.monotonic() > expiry:
            return False
        return True

    def check_api_token(self, request: WsRequest) -> bool:
        """Validate a request against the API token pool (multi-use, TTL-bound)."""
        self._purge_expired()
        token = bearer_token(request.headers) or query_first(
            parse_query(request.path), "token"
        )
        if not token:
            return False
        expiry = self._api_tokens.get(token)
        if expiry is None or time.monotonic() > expiry:
            self._api_tokens.pop(token, None)
            return False
        return True

    def check_api_token_with_identity(self, request: WsRequest) -> dict[str, str] | None:
        """Validate token and return its metadata (role, user_id). Returns None if invalid."""
        self._purge_expired()
        token = bearer_token(request.headers) or query_first(
            parse_query(request.path), "token"
        )
        if not token:
            logger.debug("[auth] check_identity: no token found in request")
            return None
        expiry = self._api_tokens.get(token)
        if expiry is None or time.monotonic() > expiry:
            self._api_tokens.pop(token, None)
            logger.debug("[auth] check_identity: token expired or not in api_tokens pool")
            return None
        meta = self._token_metadata.get(token, {})
        logger.debug("[auth] check_identity: token={} metadata={}", token[:20] + "...", meta)
        return meta

    def get_token_metadata(self, token: str) -> dict[str, str]:
        """Return metadata for a token without removing it."""
        return self._token_metadata.get(token, {})

    def revoke_token(self, token: str) -> bool:
        """Immediately invalidate a specific token. Returns True if token was found."""
        revoked = False
        if token in self._api_tokens:
            del self._api_tokens[token]
            revoked = True
        if token in self._issued_tokens:
            del self._issued_tokens[token]
            revoked = True
        if token in self._token_metadata:
            del self._token_metadata[token]
            revoked = True
        return revoked

    def revoke_user_tokens(self, role: str, user_id: str) -> int:
        """Invalidate all tokens for a specific user. Returns count of revoked tokens."""
        to_revoke = []
        for token, meta in self._token_metadata.items():
            if meta.get("role") == role and meta.get("user_id") == user_id:
                to_revoke.append(token)

        for token in to_revoke:
            self.revoke_token(token)
        return len(to_revoke)

    def pop_token_metadata(self, token: str) -> dict[str, str]:
        """Pop and return metadata for a token (used during WS handshake)."""
        return self._token_metadata.pop(token, {})

    # -- HTTP handlers -------------------------------------------------------

    def handle_token_issue_http(self, connection: Any, request: WsRequest) -> Any:
        """Handle legacy token issue endpoint."""
        if self._token_issue_secret:
            if not _issue_route_secret_matches(request.headers, self._token_issue_secret):
                return connection.respond(401, "Unauthorized")
        else:
            logger.warning(
                "websocket: token_issue_path is set but token_issue_secret is empty; "
                "any client can obtain connection tokens — set token_issue_secret for production."
            )
        self._purge_expired()
        if len(self._issued_tokens) >= _MAX_ISSUED_TOKENS:
            logger.error(
                "websocket: too many outstanding issued tokens ({}), rejecting issuance",
                len(self._issued_tokens),
            )
            return http_json_response({"error": "too many outstanding tokens"}, status=429)

        token = self.issue_token()
        return http_json_response({"token": token, "expires_in": self._token_ttl_s})

    def handle_webui_bootstrap(
        self, request: WsRequest, *, model_name: str | None = None
    ) -> Response:
        """Handle WebUI bootstrap: mint tokens for the embedded UI.

        Issues separate tokens for WebSocket and REST API:
        - ws_token: Single-use, 60s TTL, consumed at WS handshake
        - api_token: Multi-use, configurable TTL, for REST API calls
        """
        self._purge_expired()
        if (
            len(self._issued_tokens) >= _MAX_ISSUED_TOKENS
            or len(self._api_tokens) >= _MAX_ISSUED_TOKENS
        ):
            return http_response(
                http_json_response({"error": "too many outstanding tokens"}, status=429).body,
                status=429,
                content_type="application/json; charset=utf-8",
            )

        role = ""
        user_id = ""
        if request:
            query = parse_query(request.path)
            role = query_first(query, "role") or ""
            user_id = query_first(query, "user_id") or ""

        try:
            tokens = self.issue_separate_tokens(role=role, user_id=user_id)
        except RuntimeError:
            return http_json_response({"error": "too many outstanding tokens"}, status=429)

        logger.info(
            "bootstrap: issued separate tokens with role={}, user_id={}",
            role, user_id,
        )

        resp: dict[str, Any] = {
            "ws_token": tokens["ws_token"],
            "api_token": tokens["api_token"],
            "ws_path": self._ws_path,
            "expires_in": self._token_ttl_s,
            "model_name": model_name,
        }
        if role:
            resp["role"] = role
        if user_id:
            resp["user_id"] = user_id
        return http_json_response(resp)

    # -- WS handshake authorization ------------------------------------------

    def authorize_websocket_handshake(
        self, connection: Any, query: dict[str, list[str]], headers: Any = None
    ) -> Any:
        """Authorize a WebSocket handshake. Returns None on success, or an HTTP error response.

        On success, stores the token metadata on the connection object as
        ``_handshake_meta`` so that ``_connection_loop`` can retrieve it
        without re-reading the query parameters (which may not be available
        in all websockets library versions).
        """
        # Token from query parameter (websockets library doesn't pass Sec-WebSocket-Protocol to app)
        supplied = query_first(query, "token")

        if self._token:
            if supplied and hmac.compare_digest(supplied, self._token):
                return None
            if supplied and self.take_issued_token(supplied):
                # Store metadata for _connection_loop
                if supplied:
                    meta = self.get_token_metadata(supplied)
                    if meta:
                        connection._handshake_meta = dict(meta)
                return None
            return connection.respond(401, "Unauthorized")

        if self._websocket_requires_token:
            if supplied and self.take_issued_token(supplied):
                # Store metadata for _connection_loop
                if supplied:
                    meta = self.get_token_metadata(supplied)
                    if meta:
                        connection._handshake_meta = dict(meta)
                return None
            return connection.respond(401, "Unauthorized")

        if supplied:
            self.take_issued_token(supplied)
            meta = self.get_token_metadata(supplied)
            if meta:
                connection._handshake_meta = dict(meta)
        return None

    # -- User management -----------------------------------------------------

    @staticmethod
    def create_user_workspace(role: str, user_id: str) -> None:
        """Create user workspace with USER.md and directory structure."""
        templates_dir = Path.home() / ".nanobot" / "templates" / role
        if not templates_dir.is_dir():
            logger.warning("Template directory not found: {}", templates_dir)
            return

        users_dir = Path.home() / ".nanobot" / "users" / role / user_id
        if users_dir.exists():
            return

        users_dir.mkdir(parents=True, exist_ok=True)
        user_md = templates_dir / "USER.md"
        if user_md.is_file():
            shutil.copy2(user_md, users_dir / "USER.md")
        (users_dir / "sessions").mkdir(exist_ok=True)
        (users_dir / "source").mkdir(exist_ok=True)
        (users_dir / "memory").mkdir(exist_ok=True)
        logger.info("Created workspace for user: {} (role={})", user_id, role)

    @staticmethod
    def _extract_password(query: dict[str, list[str]], headers: Any = None) -> str:
        """Extract password from ``X-Password`` header (preferred), ``data`` JSON param, or query param.

        Priority order:
        1. ``X-Password`` header — keeps password completely out of URL
        2. ``data`` JSON param — keeps password out of plain URL text
        3. ``password`` query param — legacy fallback

        The header approach is most secure as it avoids URL logging entirely.
        """
        # Priority 1: X-Password header (most secure)
        if headers:
            header_password = headers.get("X-Password") or headers.get("x-password")
            if header_password:
                return header_password.strip()

        # Priority 2: data JSON param
        data = parse_mutation_data(query)
        if isinstance(data, dict):
            pw = data.get("password")
            if isinstance(pw, str) and pw:
                return pw

        # Priority 3: direct query param (legacy)
        return query_first(query, "password") or ""

    async def handle_users_register(
        self, request: WsRequest, *, storage: Any
    ) -> Response:
        """Handle user registration."""
        query = parse_query(request.path)
        role = query_first(query, "role") or ""
        user_id = query_first(query, "user_id") or ""
        display_name = query_first(query, "display_name") or user_id
        password = self._extract_password(query, request.headers)

        if not role or not user_id:
            return http_error(400, "role and user_id are required")
        if role not in ("student", "teacher", "researcher"):
            return http_error(400, "Invalid role")
        if len(user_id) > 64:
            return http_error(400, "user_id too long (max 64)")
        if not password:
            return http_error(400, "password is required")

        existing = await storage.get_user(role, user_id)
        if existing:
            return http_error(409, "User already exists")

        # Use bcrypt for password hashing (includes random salt internally)
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        user_data = {
            "role": role,
            "user_id": user_id,
            "display_name": display_name,
            "password_hash": password_hash,
            "password_salt": "",  # bcrypt embeds salt in the hash
            "registered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        user = await storage.create_user(user_data)
        self.create_user_workspace(role, user_id)

        logger.info("Registered user: {} (role={})", user_id, role)
        return http_json_response({"ok": True, "user": user})

    async def handle_users_validate(
        self, request: WsRequest, *, storage: Any
    ) -> Response:
        """Handle user validation / login."""
        query = parse_query(request.path)
        role = query_first(query, "role") or ""
        user_id = query_first(query, "user_id") or ""
        password = self._extract_password(query, request.headers)

        if not role or not user_id:
            return http_error(400, "role and user_id are required")

        user = await storage.get_user(role, user_id)
        if not user:
            return http_error(404, "User not found")

        if password and user.get("password_hash"):
            stored_hash = user.get("password_hash", "")
            if stored_hash.startswith(("$2b$", "$2a$")):
                # bcrypt hash — verify directly
                if not bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
                    return http_error(401, "Invalid password")
            else:
                # Legacy SHA-256 hash — verify then auto-upgrade to bcrypt
                salt = user.get("password_salt", "")
                expected_hash = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
                if not hmac.compare_digest(expected_hash, stored_hash):
                    return http_error(401, "Invalid password")
                # Auto-upgrade: re-hash with bcrypt and persist
                try:
                    new_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                    await storage.update_user(role, user_id, {
                        "password_hash": new_hash,
                        "password_salt": "",
                    })
                    logger.info("Auto-upgraded password hash to bcrypt for user: {} (role={})", user_id, role)
                except Exception as exc:
                    logger.warning("Failed to auto-upgrade password hash for {}: {}", user_id, exc)

        try:
            token = self.issue_token(role=role, user_id=user_id)
        except RuntimeError:
            return http_json_response({"error": "too many outstanding tokens"}, status=429)

        return http_json_response({"ok": True, "user": user, "token": token})

    async def handle_logout(
        self, request: WsRequest, *, check_identity: Any
    ) -> Response:
        """Handle user logout — revoke the current token."""
        identity = check_identity(request)
        if not identity:
            return http_error(401, "Unauthorized")

        # Extract token from Authorization header or query param
        token = bearer_token(request.headers) or query_first(
            parse_query(request.path), "token"
        )

        revoked = False
        if token:
            revoked = self.revoke_token(token)

        logger.info(
            "logout: role={}, user_id={}, token_revoked={}",
            identity.get("role"),
            identity.get("user_id"),
            revoked,
        )

        return http_json_response({"ok": True, "token_revoked": revoked})
