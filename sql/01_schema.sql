-- PostgreSQL-compatible analytical schema.
-- CSV files produced by src.transform can be loaded into these tables.

CREATE SCHEMA IF NOT EXISTS neople;

CREATE TABLE IF NOT EXISTS neople.dnf_character_snapshot (
    game_code        TEXT NOT NULL DEFAULT 'DNF',
    snapshot_date    TIMESTAMPTZ,
    server_id        TEXT,
    character_id     TEXT,
    character_name   TEXT,
    level            INTEGER,
    job_id           TEXT,
    job_grow_id      TEXT,
    job_name         TEXT,
    job_grow_name    TEXT,
    fame             NUMERIC,
    source           TEXT
);

CREATE TABLE IF NOT EXISTS neople.dnf_equipment (
    game_code        TEXT NOT NULL DEFAULT 'DNF',
    collected_at     TIMESTAMPTZ,
    character_id     TEXT,
    item_id          TEXT,
    item_name        TEXT,
    slot_id          TEXT,
    slot_name        TEXT,
    rarity           TEXT,
    reinforce        INTEGER,
    refine           INTEGER
);

CREATE TABLE IF NOT EXISTS neople.dnf_auction_sold (
    game_code        TEXT NOT NULL DEFAULT 'DNF',
    collected_at     TIMESTAMPTZ,
    item_id          TEXT,
    item_name        TEXT,
    sold_date        TIMESTAMPTZ,
    unit_price       NUMERIC,
    average_price    NUMERIC,
    count            INTEGER
);

CREATE TABLE IF NOT EXISTS neople.dnf_timeline (
    game_code        TEXT NOT NULL DEFAULT 'DNF',
    collected_at     TIMESTAMPTZ,
    character_id     TEXT,
    event_date       TIMESTAMPTZ,
    event_code       TEXT,
    event_name       TEXT,
    event_data       JSONB
);

CREATE TABLE IF NOT EXISTS neople.cyphers_player (
    game_code        TEXT NOT NULL DEFAULT 'CYPHERS',
    collected_at     TIMESTAMPTZ,
    player_id        TEXT,
    nickname         TEXT
);

CREATE TABLE IF NOT EXISTS neople.cyphers_match (
    game_code        TEXT NOT NULL DEFAULT 'CYPHERS',
    collected_at     TIMESTAMPTZ,
    player_id        TEXT,
    match_id         TEXT,
    match_date       TIMESTAMPTZ,
    game_type        TEXT
);

CREATE TABLE IF NOT EXISTS neople.cyphers_player_match_performance (
    game_code        TEXT NOT NULL DEFAULT 'CYPHERS',
    collected_at     TIMESTAMPTZ,
    match_id         TEXT,
    player_id        TEXT,
    nickname         TEXT,
    character_id     TEXT,
    character_name   TEXT,
    team             TEXT,
    result           TEXT,
    kill_count       INTEGER,
    death_count      INTEGER,
    assist_count     INTEGER
);

CREATE TABLE IF NOT EXISTS neople.cyphers_match_item (
    game_code        TEXT NOT NULL DEFAULT 'CYPHERS',
    collected_at     TIMESTAMPTZ,
    match_id         TEXT,
    player_id        TEXT,
    character_id     TEXT,
    item_id          TEXT,
    item_name        TEXT,
    slot_code        TEXT
);

CREATE INDEX IF NOT EXISTS ix_dnf_character_job_fame
    ON neople.dnf_character_snapshot (job_grow_id, fame);
CREATE INDEX IF NOT EXISTS ix_dnf_auction_item_date
    ON neople.dnf_auction_sold (item_id, sold_date);
CREATE INDEX IF NOT EXISTS ix_cyphers_performance_character
    ON neople.cyphers_player_match_performance (character_id);

