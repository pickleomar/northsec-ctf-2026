from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    backend_dir: Path
    root_dir: Path
    static_dir: Path
    fake_flag_path: Path
    port: int
    jwt_secret: str
    challenge_secret: str
    challenge_ttl_seconds: int
    token_ttl_seconds: int
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_pass: str
    db_admin_user: str
    db_admin_pass: str


@lru_cache(maxsize=1)
def load_settings() -> Settings:
    backend_dir = Path(__file__).resolve().parent
    root_dir = backend_dir.parent
    return Settings(
        backend_dir=backend_dir,
        root_dir=root_dir,
        static_dir=Path(os.environ.get("STATIC_DIR", root_dir / "dist")),
        fake_flag_path=Path(os.environ.get("FAKE_FLAG_PATH", root_dir / "flag.txt")),
        port=int(os.environ.get("PORT", "3000")),
        jwt_secret=os.environ.get("JWT_SECRET", "enpc_jwt_secret_change_me"),
        challenge_secret=os.environ.get("CHALLENGE_SECRET", secrets.token_hex(32)),
        challenge_ttl_seconds=120,
        token_ttl_seconds=60 * 60 * 24 * 7,
        db_host=os.environ.get("DB_HOST", "127.0.0.1"),
        db_port=int(os.environ.get("DB_PORT", "3306")),
        db_name=os.environ.get("DB_NAME", "enpc_game"),
        db_user=os.environ.get("DB_USER", "enpc_user"),
        db_pass=os.environ.get("DB_PASS", "enpc_pass"),
        db_admin_user=os.environ.get("DB_ADMIN_USER", "root"),
        db_admin_pass=os.environ.get("DB_ADMIN_PASS", "root"),
    )
