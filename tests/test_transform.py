import csv

import src.io_utils as io_utils
import src.transform as transform_module
from src.transform import extract_cyphers_players, nested_rows


def test_nested_rows_supports_nested_matches_object():
    payload = {"matches": {"rows": [{"matchId": "m1"}]}}
    assert nested_rows(payload, ("matches",)) == [{"matchId": "m1"}]


def test_cyphers_detail_parser_extracts_performance_and_items():
    payload = {
        "matchId": "m1",
        "players": [
            {
                "playerId": "p1",
                "nickname": "tester",
                "characterId": "c1",
                "characterName": "Character",
                "result": "win",
                "killCount": 10,
                "assistCount": 4,
                "items": [{"itemId": "i1", "itemName": "Item", "slotCode": "1"}],
            }
        ],
    }
    performance, items = extract_cyphers_players(payload, "m1", "2026-08-20T00:00:00Z")
    assert performance[0]["character_id"] == "c1"
    assert performance[0]["kill_count"] == 10
    assert items[0]["item_id"] == "i1"


def test_write_raw_preserves_repeated_collection_keys(tmp_path, monkeypatch):
    raw_dir = tmp_path / "raw"
    monkeypatch.setattr(io_utils, "RAW_DIR", raw_dir)

    first = io_utils.write_raw("dnf", "characters-fame", "same-key", {}, {"rows": []})
    second = io_utils.write_raw("dnf", "characters-fame", "same-key", {}, {"rows": []})

    assert first != second
    assert len(list((raw_dir / "dnf").glob("*.json"))) == 2


def test_dnf_detail_uses_character_id_and_server_from_params(tmp_path, monkeypatch):
    envelopes = [
        {
            "endpoint": "character_equipment",
            "key": "character_equipment_cain_character-1",
            "params": {"serverId": "cain", "characterId": "character-1"},
            "collected_at": "2026-08-23T00:00:00Z",
            "payload": {"equipment": [{"itemId": "item-1", "itemName": "Item"}]},
        }
    ]
    monkeypatch.setattr(transform_module, "read_envelopes", lambda game: envelopes)
    monkeypatch.setattr(transform_module, "PROCESSED_DIR", tmp_path)

    transform_module.transform_dnf()

    with (tmp_path / "dnf_equipment.csv").open(encoding="utf-8-sig", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert row["server_id"] == "cain"
    assert row["character_id"] == "character-1"


def test_cyphers_transform_accepts_snake_case_match_id(tmp_path, monkeypatch):
    envelopes = [
        {
            "endpoint": "matches",
            "key": "matches_player-1",
            "params": {"gameTypeId": "rating"},
            "collected_at": "2026-08-23T00:00:00Z",
            "payload": {"matches": [{"match_id": "match-2"}]},
        }
    ]
    monkeypatch.setattr(transform_module, "read_envelopes", lambda game: envelopes)
    monkeypatch.setattr(transform_module, "PROCESSED_DIR", tmp_path)

    transform_module.transform_cyphers()

    with (tmp_path / "cyphers_match.csv").open(encoding="utf-8-sig", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert row["match_id"] == "match-2"

