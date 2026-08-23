"""Export processed CSVs into a compact payload for the static web dashboard."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from .io_utils import PROCESSED_DIR, ROOT, load_config


def read_table(filename: str) -> pd.DataFrame:
    path = PROCESSED_DIR / filename
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def number(value: Any) -> int | float | None:
    if value is None or pd.isna(value):
        return None
    value = float(value)
    return int(value) if value.is_integer() else round(value, 2)


def text(value: Any, fallback: str = "미분류") -> str:
    if value is None or pd.isna(value) or str(value).strip() == "":
        return fallback
    return str(value)


def win_value(value: Any) -> bool:
    return str(value).strip().lower() in {"win", "승리", "true", "1"}


def export_dashboard() -> dict[str, Any]:
    characters = read_table("dnf_character_snapshot.csv")
    auctions = read_table("dnf_auction_sold.csv")
    performance = read_table("cyphers_player_match_performance.csv")
    match_items = read_table("cyphers_match_item.csv")

    dnf_jobs: list[dict[str, Any]] = []
    if not characters.empty:
        characters["fame_num"] = pd.to_numeric(characters.get("fame"), errors="coerce")
        characters["job_label"] = characters.apply(
            lambda row: text(row.get("job_grow_name"), text(row.get("job_name"))), axis=1
        )
        for job, group in characters.groupby("job_label", dropna=False):
            dnf_jobs.append(
                {
                    "job_name": text(job),
                    "characters": int(group["character_id"].nunique()),
                    "average_fame": number(group["fame_num"].mean()),
                    "median_fame": number(group["fame_num"].median()),
                }
            )
    dnf_jobs.sort(key=lambda row: row["median_fame"] or 0, reverse=True)

    dnf_auctions: list[dict[str, Any]] = []
    if not auctions.empty:
        auctions["price_num"] = pd.to_numeric(auctions.get("unit_price"), errors="coerce")
        auctions["item_label"] = auctions.apply(
            lambda row: text(row.get("item_name"), text(row.get("item_id"))), axis=1
        )
        for item, group in auctions.groupby("item_label", dropna=False):
            prices = group["price_num"].dropna()
            dnf_auctions.append(
                {
                    "item_name": text(item),
                    "observations": int(prices.count()),
                    "median_price": number(prices.median()),
                    "average_price": number(prices.mean()),
                }
            )
    dnf_auctions.sort(key=lambda row: row["median_price"] or 0, reverse=True)

    cyphers_characters: list[dict[str, Any]] = []
    cyphers_win_rate = None
    cyphers_matches = 0
    if not performance.empty:
        performance["win_bool"] = performance.get("result", pd.Series(dtype=str)).map(win_value)
        performance["kill_num"] = pd.to_numeric(performance.get("kill_count"), errors="coerce")
        performance["assist_num"] = pd.to_numeric(performance.get("assist_count"), errors="coerce")
        cyphers_matches = int(performance.get("match_id", pd.Series(dtype=str)).nunique())
        cyphers_win_rate = number(performance["win_bool"].mean() * 100)
        performance["character_label"] = performance.apply(
            lambda row: text(row.get("character_name"), text(row.get("character_id"))), axis=1
        )
        for character, group in performance.groupby("character_label", dropna=False):
            cyphers_characters.append(
                {
                    "character_name": text(character),
                    "matches": int(group["match_id"].nunique()),
                    "win_rate": number(group["win_bool"].mean() * 100),
                    "average_kills": number(group["kill_num"].mean()),
                    "average_assists": number(group["assist_num"].mean()),
                }
            )
    cyphers_characters.sort(key=lambda row: row["win_rate"] or 0, reverse=True)

    cyphers_items: list[dict[str, Any]] = []
    if not match_items.empty:
        match_items["item_label"] = match_items.apply(
            lambda row: text(row.get("item_name"), text(row.get("item_id"))), axis=1
        )
        for item, group in match_items.groupby("item_label", dropna=False):
            cyphers_items.append(
                {
                    "item_name": text(item),
                    "matches": int(group.get("match_id", pd.Series(dtype=str)).nunique()),
                }
            )
    cyphers_items.sort(key=lambda row: row["matches"], reverse=True)

    dnf_character_count = int(characters.get("character_id", pd.Series(dtype=str)).nunique())
    dnf_fame = pd.to_numeric(characters.get("fame"), errors="coerce") if not characters.empty else pd.Series(dtype=float)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "processed",
        "summary": {
            "dnf_characters": dnf_character_count,
            "dnf_median_fame": number(dnf_fame.median()),
            "dnf_auction_items": len(dnf_auctions),
            "cyphers_matches": cyphers_matches,
            "cyphers_win_rate": cyphers_win_rate,
        },
        "dnf": {"jobs": dnf_jobs[:12], "auctions": dnf_auctions[:12]},
        "cyphers": {"characters": cyphers_characters[:12], "items": cyphers_items[:12]},
    }


def main() -> None:
    load_config()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "web" / "data" / "dashboard.json",
        help="Output JSON path (default: web/data/dashboard.json)",
    )
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(export_dashboard(), ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    print(f"Dashboard data written to {args.output}")


if __name__ == "__main__":
    main()
