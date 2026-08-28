"""Export processed CSVs into a compact, privacy-reviewed web payload."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from .io_utils import PROCESSED_DIR, ROOT, load_config


MIN_CYPHERS_ITEM_MATCHES = 10
FAME_BANDS = (
    (float("-inf"), 50000, "50,000 미만"),
    (50000, 52000, "50,000–51,999"),
    (52000, 54000, "52,000–53,999"),
    (54000, 56000, "54,000–55,999"),
    (56000, float("inf"), "56,000 이상"),
)


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


def _column(frame: pd.DataFrame, name: str) -> pd.Series:
    if name in frame.columns:
        return frame[name]
    return pd.Series(index=frame.index, dtype=object)


def _unique_count(frame: pd.DataFrame, name: str) -> int:
    if name not in frame.columns:
        return 0
    return int(frame[name].dropna().astype(str).nunique())


def _iqr(values: pd.Series) -> float | None:
    values = pd.to_numeric(values, errors="coerce").dropna()
    if values.empty:
        return None
    return number(values.quantile(0.75) - values.quantile(0.25))


def _key(frame: pd.DataFrame, first: str, second: str) -> pd.Series:
    left = _column(frame, first).fillna("").astype(str)
    right = _column(frame, second).fillna("").astype(str)
    return left + "|" + right


def _prepare_dnf_characters(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    characters = frame.copy()
    characters["character_key"] = _key(characters, "server_id", "character_id")
    characters["fame_num"] = pd.to_numeric(_column(characters, "fame"), errors="coerce")
    characters["job_label"] = characters.apply(
        lambda row: text(row.get("job_grow_name"), text(row.get("job_name"))), axis=1
    )
    valid_ids = _column(characters, "character_id").notna() & _column(
        characters, "character_id"
    ).astype(str).ne("")
    if valid_ids.any():
        if "snapshot_date" in characters.columns:
            characters = characters.sort_values("snapshot_date")
        characters = characters.drop_duplicates("character_key", keep="last")
    return characters


def _dnf_jobs(characters: pd.DataFrame) -> list[dict[str, Any]]:
    if characters.empty:
        return []
    jobs: list[dict[str, Any]] = []
    for job, group in characters.groupby("job_label", dropna=False):
        fame = group["fame_num"].dropna()
        jobs.append(
            {
                "job_name": text(job),
                "characters": _unique_count(group, "character_key"),
                "average_fame": number(fame.mean()),
                "median_fame": number(fame.median()),
                "iqr_fame": _iqr(fame),
                "min_fame": number(fame.min()),
                "max_fame": number(fame.max()),
            }
        )
    return sorted(jobs, key=lambda row: row["median_fame"] or 0, reverse=True)


def _dnf_fame_bands(characters: pd.DataFrame) -> list[dict[str, Any]]:
    if characters.empty:
        return [
            {"band": label, "characters": 0, "median_fame": None}
            for _, _, label in FAME_BANDS
        ]
    fame = characters[["character_key", "fame_num"]].dropna(subset=["fame_num"])
    result: list[dict[str, Any]] = []
    for low, high, label in FAME_BANDS:
        selected = fame[(fame["fame_num"] >= low) & (fame["fame_num"] < high)]
        result.append(
            {
                "band": label,
                "characters": _unique_count(selected, "character_key"),
                "median_fame": number(selected["fame_num"].median()),
            }
        )
    return result


def _dnf_equipment(characters: pd.DataFrame, equipment: pd.DataFrame) -> list[dict[str, Any]]:
    if characters.empty or equipment.empty:
        return []
    items = equipment.copy()
    items["character_key"] = _key(items, "server_id", "character_id")
    items["item_label"] = items.apply(
        lambda row: text(row.get("item_name"), "이름 없는 장비"), axis=1
    )
    joined = items.merge(
        characters[["character_key", "fame_num", "job_label"]],
        on="character_key",
        how="inner",
    ).drop_duplicates(["character_key", "item_label"])
    total_characters = _unique_count(characters, "character_key")
    if total_characters == 0:
        return []
    result: list[dict[str, Any]] = []
    for item, group in joined.groupby("item_label", dropna=False):
        item_characters = _unique_count(group, "character_key")
        result.append(
            {
                "item_name": text(item),
                "characters": item_characters,
                "adoption_rate": number(item_characters / total_characters * 100),
                "median_fame": number(group["fame_num"].median()),
                "jobs": _unique_count(group, "job_label"),
            }
        )
    return sorted(result, key=lambda row: (row["adoption_rate"] or 0, row["characters"]), reverse=True)


def _dnf_auctions(auctions: pd.DataFrame) -> list[dict[str, Any]]:
    if auctions.empty:
        return []
    data = auctions.copy()
    data["price_num"] = pd.to_numeric(_column(data, "unit_price"), errors="coerce")
    data["item_label"] = data.apply(
        lambda row: text(row.get("item_name"), "이름 없는 아이템"), axis=1
    )
    result: list[dict[str, Any]] = []
    for item, group in data.groupby("item_label", dropna=False):
        prices = group["price_num"].dropna()
        mean = prices.mean() if not prices.empty else None
        stddev = prices.std(ddof=0) if not prices.empty else None
        result.append(
            {
                "item_name": text(item),
                "observations": int(prices.count()),
                "median_price": number(prices.median()),
                "average_price": number(mean),
                "price_iqr": _iqr(prices),
                "price_stddev": number(stddev),
                "price_cv": number(stddev / mean) if mean not in (None, 0) else None,
            }
        )
    return sorted(result, key=lambda row: row["median_price"] or 0, reverse=True)


def _dnf_timeline(timeline: pd.DataFrame) -> list[dict[str, Any]]:
    if timeline.empty:
        return []
    data = timeline.copy()
    data["event_label"] = data.apply(
        lambda row: text(row.get("event_name"), "이름 없는 이벤트"), axis=1
    )
    result: list[dict[str, Any]] = []
    for event, group in data.groupby("event_label", dropna=False):
        result.append(
            {
                "event_name": text(event),
                "events": int(len(group)),
                "characters": _unique_count(group, "character_id"),
            }
        )
    return sorted(result, key=lambda row: row["events"], reverse=True)


def _prepare_cyphers_performance(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    performance = frame.copy()
    performance["win_bool"] = _column(performance, "result").map(win_value)
    performance["kill_num"] = pd.to_numeric(_column(performance, "kill_count"), errors="coerce")
    performance["assist_num"] = pd.to_numeric(_column(performance, "assist_count"), errors="coerce")
    performance["character_label"] = performance.apply(
        lambda row: text(row.get("character_name"), "이름 없는 캐릭터"), axis=1
    )
    keys = [column for column in ("match_id", "player_id", "character_id") if column in performance]
    if keys:
        performance = performance.drop_duplicates(keys)
    return performance


def _cyphers_characters(performance: pd.DataFrame) -> tuple[list[dict[str, Any]], int, float | None]:
    if performance.empty:
        return [], 0, None
    matches = _unique_count(performance, "match_id")
    win_rate = number(performance["win_bool"].mean() * 100)
    result: list[dict[str, Any]] = []
    for character, group in performance.groupby("character_label", dropna=False):
        result.append(
            {
                "character_name": text(character),
                "matches": _unique_count(group, "match_id"),
                "wins": int(group["win_bool"].sum()),
                "win_rate": number(group["win_bool"].mean() * 100),
                "average_kills": number(group["kill_num"].mean()),
                "average_assists": number(group["assist_num"].mean()),
            }
        )
    return sorted(result, key=lambda row: (row["win_rate"] or 0, row["matches"]), reverse=True), matches, win_rate


def _cyphers_item_results(
    performance: pd.DataFrame, match_items: pd.DataFrame, characters: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if performance.empty or match_items.empty:
        return [], []
    items = match_items.copy()
    items["item_label"] = items.apply(
        lambda row: text(row.get("item_name"), "이름 없는 아이템"), axis=1
    )
    join_keys = [
        column
        for column in ("match_id", "player_id", "character_id")
        if column in items.columns and column in performance.columns
    ]
    if not join_keys:
        return [], []
    item_rows = items[join_keys + ["item_label"]].drop_duplicates(join_keys + ["item_label"])
    perf_rows = performance[join_keys + ["character_label", "result", "win_bool"]].drop_duplicates(join_keys)
    joined = item_rows.merge(perf_rows, on=join_keys, how="inner")
    if joined.empty:
        return [], []
    baseline = {row["character_name"]: row["win_rate"] for row in characters}
    item_performance: list[dict[str, Any]] = []
    for (character, item), group in joined.groupby(["character_label", "item_label"], dropna=False):
        item_rate = number(group["win_bool"].mean() * 100)
        character_rate = baseline.get(text(character))
        item_performance.append(
            {
                "character_name": text(character),
                "item_name": text(item),
                "matches": _unique_count(group, "match_id"),
                "win_rate": item_rate,
                "character_win_rate": character_rate,
                "lift_pp": number(item_rate - character_rate) if item_rate is not None and character_rate is not None else None,
                "enough_sample": _unique_count(group, "match_id") >= MIN_CYPHERS_ITEM_MATCHES,
            }
        )
    item_performance.sort(key=lambda row: (row["enough_sample"], row["lift_pp"] or 0), reverse=True)

    item_summary: list[dict[str, Any]] = []
    for item, group in joined.groupby("item_label", dropna=False):
        matches = _unique_count(group, "match_id")
        item_summary.append(
            {
                "item_name": text(item),
                "characters": _unique_count(group, "character_label"),
                "matches": matches,
                "win_rate": number(group["win_bool"].mean() * 100),
                "enough_sample": matches >= MIN_CYPHERS_ITEM_MATCHES,
            }
        )
    item_summary.sort(key=lambda row: (row["matches"], row["win_rate"] or 0), reverse=True)
    return item_summary, item_performance


def export_dashboard() -> dict[str, Any]:
    characters = _prepare_dnf_characters(read_table("dnf_character_snapshot.csv"))
    equipment = read_table("dnf_equipment.csv")
    auctions = read_table("dnf_auction_sold.csv")
    timeline = read_table("dnf_timeline.csv")
    performance = _prepare_cyphers_performance(read_table("cyphers_player_match_performance.csv"))
    match_items = read_table("cyphers_match_item.csv")

    dnf_jobs = _dnf_jobs(characters)
    dnf_fame_bands = _dnf_fame_bands(characters)
    dnf_equipment = _dnf_equipment(characters, equipment)
    dnf_auctions = _dnf_auctions(auctions)
    dnf_timeline = _dnf_timeline(timeline)
    cyphers_characters, cyphers_matches, cyphers_win_rate = _cyphers_characters(performance)
    cyphers_items, cyphers_item_performance = _cyphers_item_results(
        performance, match_items, cyphers_characters
    )
    dnf_fame = characters["fame_num"].dropna() if not characters.empty else pd.Series(dtype=float)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "processed",
        "summary": {
            "dnf_characters": _unique_count(characters, "character_key"),
            "dnf_median_fame": number(dnf_fame.median()),
            "dnf_auction_items": len(dnf_auctions),
            "dnf_equipment_items": len(dnf_equipment),
            "dnf_timeline_events": len(dnf_timeline),
            "cyphers_matches": cyphers_matches,
            "cyphers_win_rate": cyphers_win_rate,
            "cyphers_characters": len(cyphers_characters),
            "cyphers_items": len(cyphers_items),
        },
        "quality": {
            "raw_identifiers_excluded": True,
            "minimum_cyphers_item_matches": MIN_CYPHERS_ITEM_MATCHES,
            "notes": [
                "표본은 수집 시점과 API 호출 범위의 영향을 받습니다.",
                "승률·가격은 기술통계이며 인과관계를 의미하지 않습니다.",
                "최소 표본 수를 충족하지 못한 조합은 후보 해석에서 제외합니다.",
            ],
        },
        "dnf": {
            "jobs": dnf_jobs[:20],
            "fame_bands": dnf_fame_bands,
            "equipment": dnf_equipment[:20],
            "auctions": dnf_auctions[:20],
            "timeline": dnf_timeline[:20],
        },
        "cyphers": {
            "characters": cyphers_characters[:20],
            "items": cyphers_items[:20],
            "item_performance": cyphers_item_performance[:50],
        },
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
