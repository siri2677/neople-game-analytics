import src.collect as collect_module


def test_cyphers_collection_uses_official_ranking_without_personal_target(monkeypatch):
    values = {
        "CYPHERS_RANKING_OFFSET": "0",
        "CYPHERS_RANKING_LIMIT": "2",
        "CYPHERS_GAME_TYPE": "rating",
        "CYPHERS_START_DATE": "2026-08-01 00:00",
        "CYPHERS_END_DATE": "2026-08-28 23:59",
        "CYPHERS_MATCH_LIMIT": "1",
        "CYPHERS_MATCH_DETAIL_LIMIT": "1",
    }
    calls = []

    class FakeClient:
        def get(self, path, params=None):
            calls.append((path, params))
            if path == "/cy/ranking/ratingpoint":
                return {"rows": [{"playerId": "ranked-player-1"}]}
            if path.endswith("/matches"):
                return {"matches": [{"matchId": "match-1"}]}
            if path == "/cy/matches/match-1":
                return {"matchId": "match-1"}
            raise AssertionError(f"unexpected endpoint: {path}")

    monkeypatch.setattr(collect_module, "env", lambda name, default="": values.get(name, default))
    monkeypatch.setattr(collect_module, "write_raw", lambda *args, **kwargs: None)

    collect_module.collect_cyphers(FakeClient())

    assert calls[0] == ("/cy/ranking/ratingpoint", {"offset": 0, "limit": 2})
    assert calls[1][0] == "/cy/players/ranked-player-1/matches"
    assert calls[2][0] == "/cy/matches/match-1"
    assert not any(path == "/cy/players" for path, _ in calls)
