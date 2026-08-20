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

