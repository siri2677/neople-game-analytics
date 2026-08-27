"""Small, rate-limit-aware client for Neople Open API."""

from __future__ import annotations

import time
from typing import Any

import requests


class NeopleApiError(RuntimeError):
    """Raised when Neople API returns an unsuccessful response."""


class NeopleClient:
    def __init__(
        self,
        api_key: str,
        request_interval: float = 0.05,
        *,
        api_key_name: str = "API_KEY",
    ) -> None:
        if not api_key:
            raise ValueError(f"{api_key_name} is empty")
        self.api_key = api_key
        self.request_interval = request_interval
        self.session = requests.Session()
        self.session.headers.update({"apikey": api_key, "User-Agent": "neople-game-analytics-portfolio/1.0"})
        self._last_request_at = 0.0

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.request_interval:
            time.sleep(self.request_interval - elapsed)

        response = self.session.get(f"https://api.neople.co.kr{path}", params=params or {}, timeout=30)
        self._last_request_at = time.monotonic()
        if response.status_code != 200:
            raise NeopleApiError(f"GET {path} failed: {response.status_code} {response.text[:500]}")
        payload = response.json()
        if not isinstance(payload, dict):
            raise NeopleApiError(f"GET {path} returned non-object JSON")
        return payload

