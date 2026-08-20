-- Power BI-facing analytical views.
-- These views intentionally keep business logic in SQL rather than in visuals.

CREATE OR REPLACE VIEW neople.vw_dnf_latest_character AS
SELECT *
FROM (
    SELECT
        c.*,
        ROW_NUMBER() OVER (
            PARTITION BY c.server_id, c.character_id
            ORDER BY c.snapshot_date DESC
        ) AS latest_row_number
    FROM neople.dnf_character_snapshot c
    WHERE c.character_id IS NOT NULL
) ranked
WHERE latest_row_number = 1;

CREATE OR REPLACE VIEW neople.vw_dnf_job_growth AS
SELECT
    job_grow_id,
    MAX(job_grow_name) AS job_grow_name,
    COUNT(DISTINCT character_id) AS character_count,
    ROUND(AVG(fame), 1) AS average_fame,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY fame) AS median_fame,
    MIN(fame) AS min_fame,
    MAX(fame) AS max_fame
FROM neople.vw_dnf_latest_character
WHERE fame IS NOT NULL
GROUP BY job_grow_id;

CREATE OR REPLACE VIEW neople.vw_dnf_auction_summary AS
SELECT
    item_id,
    MAX(item_name) AS item_name,
    COUNT(*) AS observation_count,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY unit_price) AS median_unit_price,
    ROUND(AVG(unit_price), 2) AS average_unit_price,
    ROUND(STDDEV_POP(unit_price), 2) AS price_stddev,
    MIN(sold_date) AS first_sold_date,
    MAX(sold_date) AS last_sold_date
FROM neople.dnf_auction_sold
WHERE item_id IS NOT NULL
  AND unit_price IS NOT NULL
GROUP BY item_id;

CREATE OR REPLACE VIEW neople.vw_dnf_equipment_adoption AS
WITH character_counts AS (
    SELECT COUNT(DISTINCT character_id)::NUMERIC AS total_characters
    FROM neople.vw_dnf_latest_character
), item_usage AS (
    SELECT
        c.job_grow_id,
        c.job_grow_name,
        e.item_id,
        MAX(e.item_name) AS item_name,
        COUNT(DISTINCT e.character_id) AS using_characters
    FROM neople.vw_dnf_latest_character c
    JOIN neople.dnf_equipment e ON e.character_id = c.character_id
    GROUP BY c.job_grow_id, c.job_grow_name, e.item_id
)
SELECT
    u.*,
    ROUND(100 * u.using_characters / NULLIF(cc.total_characters, 0), 2) AS adoption_rate_pct
FROM item_usage u
CROSS JOIN character_counts cc;

CREATE OR REPLACE VIEW neople.vw_cyphers_character_ranking_summary AS
SELECT
    character_id,
    MAX(character_name) AS character_name,
    ranking_type,
    COUNT(*) AS ranked_player_count,
    MIN(rank) AS best_rank,
    ROUND(AVG(ranking_value), 2) AS average_ranking_value,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ranking_value) AS median_ranking_value,
    MAX(ranking_value) AS max_ranking_value
FROM neople.cyphers_character_ranking
WHERE character_id IS NOT NULL
GROUP BY character_id, ranking_type;

CREATE OR REPLACE VIEW neople.vw_cyphers_character_winrate AS
SELECT
    character_id,
    MAX(character_name) AS character_name,
    COUNT(*) AS match_count,
    SUM(CASE WHEN LOWER(COALESCE(result, '')) IN ('win', '승리', 'true') THEN 1 ELSE 0 END) AS win_count,
    ROUND(
        100.0 * SUM(CASE WHEN LOWER(COALESCE(result, '')) IN ('win', '승리', 'true') THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0),
        2
    ) AS win_rate_pct,
    ROUND(AVG(kill_count), 2) AS average_kills,
    ROUND(AVG(death_count), 2) AS average_deaths,
    ROUND(AVG(assist_count), 2) AS average_assists
FROM neople.cyphers_player_match_performance
WHERE character_id IS NOT NULL
GROUP BY character_id;

CREATE OR REPLACE VIEW neople.vw_cyphers_item_performance AS
SELECT
    p.character_id,
    MAX(p.character_name) AS character_name,
    i.item_id,
    MAX(i.item_name) AS item_name,
    COUNT(DISTINCT p.match_id) AS match_count,
    ROUND(AVG(p.kill_count), 2) AS average_kills,
    ROUND(AVG(p.assist_count), 2) AS average_assists,
    ROUND(
        100.0 * AVG(
            CASE WHEN LOWER(COALESCE(p.result, '')) IN ('win', '승리', 'true') THEN 1.0 ELSE 0.0 END
        ),
        2
    ) AS win_rate_pct
FROM neople.cyphers_player_match_performance p
JOIN neople.cyphers_match_item i
  ON i.match_id = p.match_id
 AND i.character_id = p.character_id
WHERE p.character_id IS NOT NULL
GROUP BY p.character_id, i.item_id;
