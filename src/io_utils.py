"""File and environment helpers used by collection and transformation scripts."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"


def load_config() -> None:
    load_dotenv(ROOT / ".env")


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def csv_env(name: str, default: str = "") -> list[str]:
    return [value.strip() for value in env(name, default).split(",") if value.strip()]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "unknown"


def write_raw(game: str, endpoint: str, key: str, params: dict[str, Any], payload: dict[str, Any]) -> Path:
    target_dir = RAW_DIR / game
    target_dir.mkdir(parents=True, exist_ok=True)
    # Keep every collection run. The key remains stable for transformation,
    # while the filename gets a timestamp and short nonce to avoid overwrites.
    collected_at = now_utc()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    filename = f"{safe_name(key)}_{stamp}_{uuid4().hex[:8]}.json"
    target = target_dir / filename
    envelope = {
        "collected_at": collected_at,
        "game": game,
        "endpoint": endpoint,
        "key": key,
        "params": params,
        "payload": payload,
    }
    target.write_text(json.dumps(envelope, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def read_envelopes(game: str) -> list[dict[str, Any]]:
    folder = RAW_DIR / game
    if not folder.exists():
        return []
    envelopes: list[dict[str, Any]] = []
    for path in sorted(folder.glob("*.json")):
        envelopes.append(json.loads(path.read_text(encoding="utf-8")))
    return envelopes
