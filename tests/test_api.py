import json

import apps.api.main as api_module


def test_dashboard_api_reads_reviewed_dashboard_before_demo(tmp_path, monkeypatch):
    dashboard_path = tmp_path / "dashboard.json"
    demo_path = tmp_path / "demo.json"
    dashboard_path.write_text(json.dumps({"source": "processed"}), encoding="utf-8")
    demo_path.write_text(json.dumps({"source": "demo"}), encoding="utf-8")
    monkeypatch.setattr(api_module, "DASHBOARD_PATH", dashboard_path)
    monkeypatch.setattr(api_module, "DEMO_PATH", demo_path)

    assert api_module.read_dashboard() == {"source": "processed"}
