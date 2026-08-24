"""FastAPI service that returns short-lived Power BI embed configuration."""

from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware


POWERBI_API_BASE_URL = os.getenv("POWERBI_API_BASE_URL", "https://api.powerbi.com/v1.0/myorg")
POWERBI_SCOPE = os.getenv("POWERBI_SCOPE", "https://analysis.windows.net/powerbi/api/.default")

app = FastAPI(title="Neople Analytics API", version="0.1.0")

allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:8080").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value or value.startswith("replace_with_"):
        raise HTTPException(status_code=503, detail=f"{name} is not configured")
    return value


async def get_entra_access_token(client: httpx.AsyncClient) -> str:
    tenant_id = required("POWERBI_TENANT_ID")
    response = await client.post(
        f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
        data={
            "client_id": required("POWERBI_CLIENT_ID"),
            "client_secret": required("POWERBI_CLIENT_SECRET"),
            "scope": POWERBI_SCOPE,
            "grant_type": "client_credentials",
        },
    )
    if response.is_error:
        raise HTTPException(status_code=502, detail="Microsoft Entra token request failed")
    payload = response.json()
    access_token = payload.get("access_token")
    if not access_token:
        raise HTTPException(status_code=502, detail="Microsoft Entra token was missing")
    return access_token


async def powerbi_request(
    client: httpx.AsyncClient,
    method: str,
    path: str,
    access_token: str,
    **kwargs: Any,
) -> dict[str, Any]:
    response = await client.request(
        method,
        f"{POWERBI_API_BASE_URL}{path}",
        headers={"Authorization": f"Bearer {access_token}"},
        **kwargs,
    )
    if response.is_error:
        raise HTTPException(status_code=502, detail="Power BI API request failed")
    return response.json()


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/powerbi/embed-config")
async def embed_config() -> dict[str, Any]:
    workspace_id = required("POWERBI_WORKSPACE_ID")
    report_id = required("POWERBI_REPORT_ID")
    async with httpx.AsyncClient(timeout=20.0) as client:
        access_token = await get_entra_access_token(client)
        report = await powerbi_request(
            client,
            "GET",
            f"/groups/{workspace_id}/reports/{report_id}",
            access_token,
        )
        embed = await powerbi_request(
            client,
            "POST",
            f"/groups/{workspace_id}/reports/{report_id}/GenerateToken",
            access_token,
            json={
                "accessLevel": "View",
                "lifetimeInMinutes": int(os.getenv("POWERBI_TOKEN_LIFETIME_MINUTES", "30")),
            },
        )
    return {
        "type": "report",
        "embedUrl": report["embedUrl"],
        "reportId": report["id"],
        "accessToken": embed["token"],
        "expiration": embed.get("expiration"),
    }
