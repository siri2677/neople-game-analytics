"""Run the scheduled collection, transformation, and public export pipeline."""

from __future__ import annotations

import json
from pathlib import Path

from .collect import collect_cyphers, collect_dnf
from .io_utils import ROOT, env, load_config
from .neople_api import NeopleClient
from .transform import transform_cyphers, transform_dnf
from .web_export import export_dashboard


def dashboard_path() -> Path:
    configured = Path(env("PUBLIC_DASHBOARD_PATH", "data/public/dashboard.json"))
    return configured if configured.is_absolute() else ROOT / configured


def main() -> None:
    load_config()
    dnf_client = NeopleClient(env("DNF_API_KEY"), api_key_name="DNF_API_KEY")
    cyphers_client = NeopleClient(
        env("CYPHERS_API_KEY"), api_key_name="CYPHERS_API_KEY"
    )

    collect_dnf(dnf_client)
    collect_cyphers(cyphers_client)
    transform_dnf()
    transform_cyphers()

    output = dashboard_path()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(export_dashboard(), ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    print(f"Public dashboard written to {output}")


if __name__ == "__main__":
    main()
