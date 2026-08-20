"""Collect a bounded, reproducible sample from DNF and Cyphers APIs.

The collector intentionally requires an explicit target list or bounded fame bands.
It does not crawl the whole service.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from typing import Any

from .io_utils import csv_env, env, load_config, write_raw
from .neople_api import NeopleClient


def parse_bands() -> list[tuple[int, int]]:
    bands = []
    for value in csv_env("DNF_FAME_BANDS", "50000:52000"):
        low, high = value.split(":", 1)
        bands.append((int(low), int(high)))
    return bands


def rows(payload: dict[str, Any], *keys: str) -> list[dict[str, Any]]:
    for key in keys:
        candidate = payload.get(key)
        if isinstance(candidate, list):
            return [item for item in candidate if isinstance(item, dict)]
        if isinstance(candidate, dict):
            nested = rows(candidate, "rows", "matches", "timeline")
            if nested:
                return nested
    return []


def collect_dnf(client: NeopleClient, dry_run: bool = False) -> None:
    servers = csv_env("DNF_SERVERS", "all")
    sample_limit = int(env("DNF_SAMPLE_LIMIT", "30"))
    auction_limit = int(env("DNF_AUCTION_ITEM_LIMIT", "30"))
    discovered_items: dict[str, str] = {}

    for server in servers:
        for low, high in parse_bands():
            params = {"serverId": server, "minFame": low, "maxFame": high, "limit": sample_limit}
            if dry_run:
                print("DNF fame search", params)
                continue
            payload = client.get("/df/servers/{}/characters-fame".format(server), params)
            write_raw("dnf", "characters-fame", f"fame_{server}_{low}_{high}", params, payload)
            for character in rows(payload, "rows"):
                character_id = character.get("characterId")
                character_server = character.get("serverId", server)
                if not character_id:
                    continue
                base = f"/df/servers/{character_server}/characters/{character_id}"
                detail_calls = {
                    "character_basic": base,
                    "character_equipment": f"{base}/equip/equipment",
                    "character_timeline": f"{base}/timeline",
                }
                detail_payloads: dict[str, dict[str, Any]] = {}
                for name, endpoint in detail_calls.items():
                    if dry_run:
                        print(name, endpoint)
                        continue
                    detail = client.get(endpoint)
                    detail_payloads[name] = detail
                    detail_params = {"serverId": character_server, "characterId": character_id}
                    write_raw("dnf", name, f"{name}_{character_server}_{character_id}", detail_params, detail)
                if not dry_run:
                    # The equipment response was already collected above. Reusing the
                    # raw file avoids an unnecessary duplicate API request.
                    equipment_payload = detail_payloads.get("character_equipment", {})
                    for item in rows(equipment_payload, "equipment"):
                        item_id = item.get("itemId")
                        item_name = item.get("itemName")
                        if item_id:
                            discovered_items[item_id] = item_name or item_id

    for item_id, item_name in list(discovered_items.items())[:auction_limit]:
        params = {"itemId": item_id, "limit": 100}
        if dry_run:
            print("DNF auction sold", params, item_name)
        else:
            payload = client.get("/df/auction-sold", params)
            write_raw("dnf", "auction_sold", f"auction_sold_{item_id}", params, payload)


def collect_cyphers(client: NeopleClient, dry_run: bool = False) -> None:
    player_ids = csv_env("CYPHERS_PLAYER_IDS")
    nicknames = csv_env("CYPHERS_NICKNAMES")
    game_type = env("CYPHERS_GAME_TYPE", "rating")
    end_date = env("CYPHERS_END_DATE") or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    start_date = env("CYPHERS_START_DATE") or (
        datetime.now(timezone.utc) - timedelta(days=30)
    ).strftime("%Y-%m-%d %H:%M")
    match_limit = int(env("CYPHERS_MATCH_LIMIT", "50"))
    detail_limit = int(env("CYPHERS_MATCH_DETAIL_LIMIT", "100"))

    for nickname in nicknames:
        params = {"nickname": nickname, "wordType": "match", "limit": 10}
        if dry_run:
            print("Cyphers player search", params)
        else:
            payload = client.get("/cy/players", params)
            write_raw("cyphers", "players", f"player_search_{nickname}", params, payload)
            for player in rows(payload, "rows"):
                if player.get("playerId") and player["playerId"] not in player_ids:
                    player_ids.append(player["playerId"])

    if not player_ids:
        print("Cyphers: no player IDs configured; set CYPHERS_PLAYER_IDS or CYPHERS_NICKNAMES")
        return

    match_ids: list[str] = []
    for player_id in player_ids:
        params = {
            "gameTypeId": game_type,
            "startDate": start_date,
            "endDate": end_date,
            "limit": match_limit,
        }
        endpoint = f"/cy/players/{player_id}/matches"
        if dry_run:
            print("Cyphers matches", endpoint, params)
            continue
        payload = client.get(endpoint, params)
        write_raw("cyphers", "matches", f"matches_{player_id}", params, payload)
        for match in rows(payload, "matches", "rows"):
            match_id = match.get("matchId") or match.get("match_id")
            if match_id and match_id not in match_ids:
                match_ids.append(match_id)

    for match_id in match_ids[:detail_limit]:
        endpoint = f"/cy/matches/{match_id}"
        if dry_run:
            print("Cyphers match detail", endpoint)
        else:
            payload = client.get(endpoint)
            write_raw("cyphers", "match_detail", f"match_detail_{match_id}", {}, payload)


def main() -> None:
    load_config()
    parser = argparse.ArgumentParser()
    parser.add_argument("--game", choices=["dnf", "cyphers", "all"], default="all")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.dry_run:
        client = None
    else:
        client = NeopleClient(env("NEOPLE_API_KEY"))
    if args.game in {"dnf", "all"}:
        collect_dnf(client, args.dry_run)  # type: ignore[arg-type]
    if args.game in {"cyphers", "all"}:
        collect_cyphers(client, args.dry_run)  # type: ignore[arg-type]


if __name__ == "__main__":
    main()
