from __future__ import annotations

import time
from functools import wraps
from typing import Any

import jwt
from flask import jsonify, request

from .config import load_settings


def issue_jwt(user_id: int, username: str) -> str:
    settings = load_settings()
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "username": username,
        "iat": now,
        "exp": now + settings.token_ttl_seconds,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def require_auth(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return jsonify({"error": "Unauthorized"}), 401

        token = header.removeprefix("Bearer ").strip()
        settings = load_settings()
        try:
            payload: dict[str, Any] = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
            request.user_id = int(payload["sub"])  # type: ignore[attr-defined]
            request.username = str(payload["username"])  # type: ignore[attr-defined]
        except Exception:
            return jsonify({"error": "Unauthorized"}), 401

        return view(*args, **kwargs)

    return wrapped
