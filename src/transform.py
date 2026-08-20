"""Flatten collected API envelopes into Power BI-ready CSV files."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from .io_utils import PROCESSED_DIR, load_config, read_envelopes


def nested_rows(payload: dict[str, Any], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]
        if isinstance(value, dict):
            result = nested_rows(value, ("rows", "matches", "timeline"))
            if result:
                return result
    return []


def first(row: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if row.get(key) is not None:
            return row[key]
    return default


def walk_dicts(value: Any) -> list[dict[str, Any]]:
    """Return every nested dictionary once, preserving the API response shape."""
    found: list[dict[str, Any]] = []
    if isinstance(value, dict):
        found.append(value)
        for child in value.values():
            found.extend(walk_dicts(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(walk_dicts(child))
    return found


def extract_cyphers_players(payload: dict[str, Any], match_id: str, collected_at: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Best-effort parser for player and item records in a match detail response.

    The raw detail JSON is always retained. This parser only creates convenience
    tables for the common fields used in the first Power BI version.
    """
    performance: list[dict[str, Any]] = []
    item_rows: list[dict[str, Any]] = []
    seen_players: set[tuple[Any, Any]] = set()
    for candidate in walk_dicts(payload):
        if not candidate.get("characterId"):
            continue
        marker = (candidate.get("playerId"), candidate.get("characterId"))
        if marker in seen_players:
            continue
        seen_players.add(marker)
        result = first(candidate, "result", "win", "isWin", "outcome")
        if isinstance(result, bool):
            result = "win" if result else "loss"
        performance.append({
            "game_code": "CYPHERS",
            "collected_at": collected_at,
            "match_id": match_id,
            "player_id": first(candidate, "playerId"),
            "nickname": first(candidate, "nickname", "playerName"),
            "character_id": first(candidate, "characterId"),
            "character_name": first(candidate, "characterName"),
            "team": first(candidate, "team", "teamId"),
            "result": result,
            "kill_count": first(candidate, "killCount", "kill"),
            "death_count": first(candidate, "deathCount", "death"),
            "assist_count": first(candidate, "assistCount", "assist"),
        })
        for nested in walk_dicts(candidate):
            item_id = nested.get("itemId")
            if item_id:
                item_rows.append({
                    "game_code": "CYPHERS",
                    "collected_at": collected_at,
                    "match_id": match_id,
                    "player_id": first(candidate, "playerId"),
                    "character_id": first(candidate, "characterId"),
                    "item_id": item_id,
                    "item_name": first(nested, "itemName", "name"),
                    "slot_code": first(nested, "slotCode", "slotId"),
                })
    return performance, item_rows


def transform_dnf() -> None:
    envelopes = read_envelopes("dnf")
    characters: list[dict[str, Any]] = []
    equipment: list[dict[str, Any]] = []
    auctions: list[dict[str, Any]] = []
    timeline: list[dict[str, Any]] = []

    for envelope in envelopes:
        endpoint = envelope.get("endpoint", "")
        params = envelope.get("params", {})
        payload = envelope.get("payload", {})
        collected_at = envelope.get("collected_at")

        if endpoint == "characters-fame":
            for row in nested_rows(payload, ("rows",)):
                characters.append({
                    "game_code": "DNF",
                    "snapshot_date": collected_at,
                    "server_id": first(row, "serverId", default=params.get("serverId")),
                    "character_id": first(row, "characterId"),
                    "character_name": first(row, "characterName"),
                    "level": first(row, "level"),
                    "job_id": first(row, "jobId"),
                    "job_grow_id": first(row, "jobGrowId"),
                    "job_name": first(row, "jobName"),
                    "job_grow_name": first(row, "jobGrowName"),
                    "fame": first(row, "fame", "adventureFame"),
                    "source": "characters-fame",
                })
        elif endpoint == "character_basic":
            for row in [payload]:
                characters.append({
                    "game_code": "DNF",
                    "snapshot_date": collected_at,
                    "server_id": first(row, "serverId", default=envelope.get("params", {}).get("serverId")),
                    "character_id": first(row, "characterId"),
                    "character_name": first(row, "characterName"),
                    "level": first(row, "level"),
                    "job_id": first(row, "jobId"),
                    "job_grow_id": first(row, "jobGrowId"),
                    "job_name": first(row, "jobName"),
                    "job_grow_name": first(row, "jobGrowName"),
                    "fame": first(row, "fame", "adventureFame"),
                    "source": "character-basic",
                })
        elif endpoint == "character_equipment":
            character_id = envelope["key"].replace("character_equipment_", "") if "key" in envelope else None
            for row in nested_rows(payload, ("equipment", "rows")):
                equipment.append({
                    "game_code": "DNF",
                    "collected_at": collected_at,
                    "character_id": character_id,
                    "item_id": first(row, "itemId"),
                    "item_name": first(row, "itemName"),
                    "slot_id": first(row, "slotId"),
                    "slot_name": first(row, "slotName"),
                    "rarity": first(row, "rarity"),
                    "reinforce": first(row, "reinforce"),
                    "refine": first(row, "refine"),
                })
        elif endpoint == "auction_sold":
            for row in nested_rows(payload, ("rows",)):
                auctions.append({
                    "game_code": "DNF",
                    "collected_at": collected_at,
                    "item_id": first(row, "itemId", default=params.get("itemId")),
                    "item_name": first(row, "itemName"),
                    "sold_date": first(row, "soldDate", "date"),
                    "unit_price": first(row, "unitPrice", "price"),
                    "average_price": first(row, "averagePrice"),
                    "count": first(row, "count"),
                })
        elif endpoint == "character_timeline":
            character_id = envelope["key"].replace("character_timeline_", "") if "key" in envelope else None
            for row in nested_rows(payload, ("timeline", "rows")):
                timeline.append({
                    "game_code": "DNF",
                    "collected_at": collected_at,
                    "character_id": character_id,
                    "event_date": first(row, "date", "eventDate"),
                    "event_code": first(row, "code"),
                    "event_name": first(row, "name"),
                    "event_data": str(first(row, "data", default={})),
                })

    write_csv(characters, "dnf_character_snapshot.csv")
    write_csv(equipment, "dnf_equipment.csv")
    write_csv(auctions, "dnf_auction_sold.csv")
    write_csv(timeline, "dnf_timeline.csv")


def transform_cyphers() -> None:
    envelopes = read_envelopes("cyphers")
    players: list[dict[str, Any]] = []
    matches: list[dict[str, Any]] = []
    details: list[dict[str, Any]] = []
    performance: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []

    for envelope in envelopes:
        endpoint = envelope.get("endpoint", "")
        payload = envelope.get("payload", {})
        collected_at = envelope.get("collected_at")
        params = envelope.get("params", {})
        if endpoint == "players":
            for row in nested_rows(payload, ("rows",)):
                players.append({
                    "game_code": "CYPHERS",
                    "collected_at": collected_at,
                    "player_id": first(row, "playerId"),
                    "nickname": first(row, "nickname", "playerName"),
                })
        elif endpoint == "matches":
            for row in nested_rows(payload, ("matches", "rows")):
                matches.append({
                    "game_code": "CYPHERS",
                    "collected_at": collected_at,
                    "player_id": envelope.get("key", "").replace("matches_", ""),
                    "match_id": first(row, "matchId"),
                    "match_date": first(row, "date", "matchDate"),
                    "game_type": first(row, "gameTypeId", default=params.get("gameTypeId")),
                })
        elif endpoint == "match_detail":
            match_id = envelope.get("key", "").replace("match_detail_", "")
            # Keep the complete detail as JSON text. This preserves fields that may change
            # and lets Power BI or a later parser use them without losing raw evidence.
            details.append({
                "game_code": "CYPHERS",
                "collected_at": collected_at,
                "match_id": match_id,
                "match_detail_json": json.dumps(payload, ensure_ascii=False),
            })
            parsed_performance, parsed_items = extract_cyphers_players(payload, match_id, collected_at)
            performance.extend(parsed_performance)
            items.extend(parsed_items)

    write_csv(players, "cyphers_player.csv")
    write_csv(matches, "cyphers_match.csv")
    write_csv(details, "cyphers_match_detail_raw.csv")
    write_csv(performance, "cyphers_player_match_performance.csv")
    write_csv(items, "cyphers_match_item.csv")


def write_csv(rows: list[dict[str, Any]], filename: str) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    columns = {
        "dnf_character_snapshot.csv": [
            "game_code", "snapshot_date", "server_id", "character_id", "character_name",
            "level", "job_id", "job_grow_id", "job_name", "job_grow_name", "fame", "source",
        ],
        "dnf_equipment.csv": [
            "game_code", "collected_at", "character_id", "item_id", "item_name", "slot_id",
            "slot_name", "rarity", "reinforce", "refine",
        ],
        "dnf_auction_sold.csv": [
            "game_code", "collected_at", "item_id", "item_name", "sold_date", "unit_price",
            "average_price", "count",
        ],
        "dnf_timeline.csv": [
            "game_code", "collected_at", "character_id", "event_date", "event_code",
            "event_name", "event_data",
        ],
        "cyphers_player.csv": ["game_code", "collected_at", "player_id", "nickname"],
        "cyphers_match.csv": [
            "game_code", "collected_at", "player_id", "match_id", "match_date", "game_type",
        ],
        "cyphers_match_detail_raw.csv": ["game_code", "collected_at", "match_id", "match_detail_json"],
        "cyphers_player_match_performance.csv": [
            "game_code", "collected_at", "match_id", "player_id", "nickname", "character_id",
            "character_name", "team", "result", "kill_count", "death_count", "assist_count",
        ],
        "cyphers_match_item.csv": [
            "game_code", "collected_at", "match_id", "player_id", "character_id", "item_id",
            "item_name", "slot_code",
        ],
    }.get(filename)
    frame = pd.DataFrame(rows, columns=columns)
    frame.to_csv(PROCESSED_DIR / filename, index=False, encoding="utf-8-sig")


def main() -> None:
    load_config()
    transform_dnf()
    transform_cyphers()
    print(f"Processed files written to {PROCESSED_DIR}")


if __name__ == "__main__":
    main()
