"""Read-only API for the public dashboard payload.

The API process serves the reviewed JSON from the shared data volume (or the
bundled demo payload). Collection runs in a separate Worker process using the
same image, so API requests never need Neople credentials.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException


APP_ROOT = Path(os.getenv("APP_ROOT", "/app"))
configured_dashboard_path = Path(
    os.getenv("PUBLIC_DASHBOARD_PATH", "data/public/dashboard.json")
)
DASHBOARD_PATH = (
    configured_dashboard_path
    if configured_dashboard_path.is_absolute()
    else APP_ROOT / configured_dashboard_path
)
DEMO_PATH = APP_ROOT / "bootstrap" / "demo.json"

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
