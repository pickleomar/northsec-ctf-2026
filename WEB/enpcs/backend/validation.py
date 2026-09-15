from __future__ import annotations

import base64
import hashlib
import hmac
import time
from pathlib import Path
from typing import Any

from .config import load_settings


def issue_challenge(seed: int) -> dict[str, Any]:
    settings = load_settings()
    issued_at = int(time.time())
    payload = f"{seed}:{issued_at}"
    signature = hmac.new(
        settings.challenge_secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    token = base64.urlsafe_b64encode(f"{payload}:{signature}".encode("utf-8")).decode(
        "ascii"
    )
    return {"token": token, "expiresAt": issued_at + settings.challenge_ttl_seconds}


def verify_challenge(token: str, seed: int) -> bool:
    settings = load_settings()
    try:
        decoded = base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8")
        token_seed_raw, issued_at_raw, signature = decoded.split(":", 2)
        token_seed = int(token_seed_raw)
        issued_at = int(issued_at_raw)
    except Exception:
        return False

    if token_seed != seed:
        return False

    now = int(time.time())
    if issued_at > now or now - issued_at > settings.challenge_ttl_seconds:
        return False

    payload = f"{token_seed}:{issued_at}"
    expected = hmac.new(
        settings.challenge_secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(signature, expected)


def compute_loss(positions: list[list[float]]) -> float:
    if not positions:
        return 1.0
    total = 0.0
    for x, y in positions:
        diff = y - x
        total += diff * diff
    return total / len(positions)


def clamp(value: float, lower: float, upper: float) -> float:
    return lower if value < lower else upper if value > upper else value


def sanitize_payload(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None

    required = {"positions", "model", "stage", "seed", "challengeToken"}
    if not required.issubset(payload.keys()):
        return None

    try:
        seed = int(payload["seed"])
    except Exception:
        return None

    challenge_token = payload.get("challengeToken")
    if not isinstance(challenge_token, str) or not verify_challenge(challenge_token, seed):
        return None

    positions = payload.get("positions")
    if not isinstance(positions, list) or not positions or len(positions) > 250:
        return None

    stage = payload.get("stage")
    if not isinstance(stage, dict):
        return None

    try:
        width = float(stage["w"])
        height = float(stage["h"])
    except Exception:
        return None

    if not (100.0 <= width <= 4000.0 and 100.0 <= height <= 4000.0):
        return None

    model = payload.get("model")
    if not isinstance(model, dict):
        return None

    cleaned_model: dict[str, float] = {}
    for key in ("m", "b", "noise", "lr"):
        try:
            cleaned_model[key] = float(model[key])
        except Exception:
            return None

    cleaned_positions: list[list[float]] = []
    for point in positions:
        if not (isinstance(point, (list, tuple)) and len(point) == 2):
            return None
        try:
            x = clamp(float(point[0]), 0.0, width)
            y = clamp(float(point[1]), 0.0, height)
        except Exception:
            return None
        cleaned_positions.append([x, y])

    return {
        "positions": cleaned_positions,
        "model": cleaned_model,
        "stage": {"w": width, "h": height},
        "seed": seed,
    }


def read_fake_flag() -> str:
    settings = load_settings()
    outfile_path = Path("/flag.txt")
    target_path = outfile_path if outfile_path.exists() else settings.fake_flag_path
    return target_path.read_text(encoding="utf-8").strip()
