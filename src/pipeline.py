"""Run one reproducible collection, transform, and PostgreSQL load cycle."""

from __future__ import annotations

import os

from .collect import collect_cyphers, collect_dnf
from .io_utils import env, load_config
from .load_postgres import load
from .neople_api import NeopleClient
from .transform import transform_cyphers, transform_dnf


def main() -> None:
    load_config()
    client = NeopleClient(env("NEOPLE_API_KEY"))
    collect_dnf(client)
    collect_cyphers(client)
    transform_dnf()
    transform_cyphers()
    load(os.getenv("PIPELINE_LOAD_MODE", "replace"))
    print("Analytics pipeline completed")


if __name__ == "__main__":
    main()
