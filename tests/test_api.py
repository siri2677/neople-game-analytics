from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_healthz():
    response = TestClient(app).get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_embed_config_reports_missing_powerbi_configuration(monkeypatch):
    for name in (
        "POWERBI_TENANT_ID",
        "POWERBI_CLIENT_ID",
        "POWERBI_CLIENT_SECRET",
        "POWERBI_WORKSPACE_ID",
        "POWERBI_REPORT_ID",
    ):
        monkeypatch.delenv(name, raising=False)
    response = TestClient(app).get("/api/powerbi/embed-config")
    assert response.status_code == 503
    assert "POWERBI_WORKSPACE_ID" in response.json()["detail"]
