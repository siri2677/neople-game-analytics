import pandas as pd

import src.web_export as web_export


def test_export_dashboard_contains_analysis_ready_aggregates(monkeypatch):
    tables = {
        "dnf_character_snapshot.csv": pd.DataFrame(
            [
                {"server_id": "cain", "character_id": "c1", "character_name": "A", "job_name": "전사", "job_grow_name": "검귀", "fame": 50000},
                {"server_id": "cain", "character_id": "c2", "character_name": "B", "job_name": "전사", "job_grow_name": "검귀", "fame": 54000},
                {"server_id": "cain", "character_id": "c3", "character_name": "C", "job_name": "마법사", "job_grow_name": "아수라", "fame": 52000},
            ]
        ),
        "dnf_equipment.csv": pd.DataFrame(
            [
                {"server_id": "cain", "character_id": "c1", "item_id": "i1", "item_name": "장비 A"},
                {"server_id": "cain", "character_id": "c2", "item_id": "i1", "item_name": "장비 A"},
                {"server_id": "cain", "character_id": "c3", "item_id": "i2", "item_name": "장비 B"},
            ]
        ),
        "dnf_auction_sold.csv": pd.DataFrame(
            [
                {"item_id": "i1", "item_name": "장비 A", "unit_price": 100},
                {"item_id": "i1", "item_name": "장비 A", "unit_price": 200},
                {"item_id": "i1", "item_name": "장비 A", "unit_price": 300},
            ]
        ),
        "dnf_timeline.csv": pd.DataFrame(
            [
                {"character_id": "c1", "event_code": "upgrade", "event_name": "장비 강화"},
                {"character_id": "c2", "event_code": "upgrade", "event_name": "장비 강화"},
            ]
        ),
        "cyphers_player_match_performance.csv": pd.DataFrame(
            [
                {"match_id": "m1", "player_id": "p1", "character_id": "c1", "character_name": "티엔", "result": "win", "kill_count": 4, "assist_count": 6},
                {"match_id": "m2", "player_id": "p1", "character_id": "c1", "character_name": "티엔", "result": "loss", "kill_count": 2, "assist_count": 4},
                {"match_id": "m3", "player_id": "p2", "character_id": "c2", "character_name": "테이", "result": "win", "kill_count": 5, "assist_count": 3},
            ]
        ),
        "cyphers_match_item.csv": pd.DataFrame(
            [
                {"match_id": "m1", "player_id": "p1", "character_id": "c1", "item_id": "ci1", "item_name": "공격킷"},
                {"match_id": "m2", "player_id": "p1", "character_id": "c1", "item_id": "ci1", "item_name": "공격킷"},
                {"match_id": "m3", "player_id": "p2", "character_id": "c2", "item_id": "ci2", "item_name": "방어킷"},
            ]
        ),
    }

    monkeypatch.setattr(web_export, "read_table", lambda filename: tables.get(filename, pd.DataFrame()))

    result = web_export.export_dashboard()

    assert result["summary"]["dnf_characters"] == 3
    assert result["dnf"]["jobs"][0]["median_fame"] == 52000
    assert result["dnf"]["fame_bands"][1]["characters"] == 1
    assert result["dnf"]["equipment"][0]["adoption_rate"] == 66.67
    assert result["dnf"]["auctions"][0]["price_iqr"] == 100
    assert result["dnf"]["auctions"][0]["price_cv"] == 0.41
    assert result["dnf"]["timeline"][0]["events"] == 2
    assert result["cyphers"]["characters"][0]["win_rate"] == 100
    assert result["cyphers"]["items"][0]["matches"] == 2
    assert result["cyphers"]["item_performance"][0]["lift_pp"] == 0


def test_export_dashboard_marks_small_cyphers_item_samples_and_excludes_identifiers(monkeypatch):
    tables = {
        "cyphers_player_match_performance.csv": pd.DataFrame(
            [{"match_id": "m1", "player_id": "p1", "character_id": "c1", "result": "win"}]
        ),
        "cyphers_match_item.csv": pd.DataFrame(
            [{"match_id": "m1", "player_id": "p1", "character_id": "c1", "item_id": "i1"}]
        ),
    }
    monkeypatch.setattr(web_export, "read_table", lambda filename: tables.get(filename, pd.DataFrame()))

    result = web_export.export_dashboard()
    item_result = result["cyphers"]["item_performance"][0]

    assert item_result["enough_sample"] is False
    assert result["quality"]["raw_identifiers_excluded"] is True

    serialized = str(result)
    for forbidden in ("player_id", "character_id", "item_id", "nickname", "match_detail_json"):
        assert forbidden not in serialized
    for identifier in ("p1", "c1", "i1"):
        assert identifier not in serialized
