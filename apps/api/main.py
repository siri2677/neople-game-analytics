"""Read-only API for the static dashboard payload.

This service deliberately does not collect from Neople or expose API keys.
The collector remains a separate local/CI data-preparation step, while this
API only serves the reviewed dashboard JSON bundled or mounted into the image.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException


DATA_DIR = Path(os.getenv("DASHBOARD_DATA_DIR", "/app/data"))
DASHBOARD_PATH = DATA_DIR / "dashboard.json"
DEMO_PATH = DATA_DIR / "demo.json"

app = FastAPI(title="Neople Game Analytics API", version="1.0.0")


def data_path() -> Path:
    if DASHBOARD_PATH.exists():
        return DASHBOARD_PATH
    return DEMO_PATH


def read_dashboard() -> dict[str, Any]:
    path = data_path()
    if not path.exists():
        raise HTTPException(status_code=503, detail="dashboard data is not available")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise HTTPException(status_code=503, detail="dashboard data could not be read") from error
    if not isinstance(payload, dict):
        raise HTTPException(status_code=503, detail="dashboard data must be a JSON object")
    return payload


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/dashboard")
async def dashboard() -> dict[str, Any]:
    return read_dashboard()
