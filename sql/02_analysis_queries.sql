-- Portfolio analysis queries.
-- These queries are also suitable as Power BI source views.

-- 1. DNF: latest fame snapshot per character.
WITH ranked AS (
    SELECT
        c.*,
        ROW_NUMBER() OVER (
            PARTITION BY c.server_id, c.character_id
            ORDER BY c.snapshot_date DESC
        ) AS rn
    FROM neople.dnf_character_snapshot c
    WHERE c.fame IS NOT NULL
)
SELECT *
FROM ranked
WHERE rn = 1;

-- 2. DNF: job growth distribution.
SELECT
    job_grow_name,
    COUNT(DISTINCT character_id) AS characters,
    ROUND(AVG(fame), 1) AS avg_fame,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY fame) AS median_fame,
    MIN(fame) AS min_fame,
    MAX(fame) AS max_fame
FROM neople.dnf_character_snapshot
WHERE fame IS NOT NULL
GROUP BY job_grow_name
ORDER BY median_fame DESC;

-- 3. DNF: equipment adoption by job and fame band.
WITH latest_character AS (
    SELECT DISTINCT ON (server_id, character_id)
        server_id, character_id, job_grow_name, fame
    FROM neople.dnf_character_snapshot
    WHERE fame IS NOT NULL
    ORDER BY server_id, character_id, snapshot_date DESC
), usage AS (
    SELECT
        c.job_grow_name,
        WIDTH_BUCKET(c.fame, 0, 60000, 6) AS fame_band,
        e.item_id,
        MAX(e.item_name) AS item_name,
        COUNT(DISTINCT c.character_id) AS character_count
    FROM latest_character c
    JOIN neople.dnf_equipment e ON e.character_id = c.character_id
    GROUP BY c.job_grow_name, WIDTH_BUCKET(c.fame, 0, 60000, 6), e.item_id
)
SELECT *,
       RANK() OVER (
           PARTITION BY job_grow_name, fame_band
           ORDER BY character_count DESC
       ) AS item_rank
FROM usage;

-- 4. DNF: auction price summary and robust price dispersion.
SELECT
    item_id,
    MAX(item_name) AS item_name,
    COUNT(*) AS observations,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY unit_price) AS median_unit_price,
    AVG(unit_price) AS avg_unit_price,
    STDDEV_POP(unit_price) AS price_stddev,
    MIN(sold_date) AS first_sold_date,
    MAX(sold_date) AS last_sold_date
FROM neople.dnf_auction_sold
WHERE unit_price IS NOT NULL
GROUP BY item_id
HAVING COUNT(*) >= 3
ORDER BY median_unit_price DESC;

-- 5. DNF: timeline events per character, useful as descriptive evidence.
SELECT
    character_id,
    event_code,
    MAX(event_name) AS event_name,
    COUNT(*) AS event_count,
    MIN(event_date) AS first_event_date,
    MAX(event_date) AS last_event_date
FROM neople.dnf_timeline
GROUP BY character_id, event_code
ORDER BY event_count DESC;

-- 6. Cyphers: official character ranking distribution.
SELECT
    character_id,
    MAX(character_name) AS character_name,
    ranking_type,
    COUNT(*) AS ranked_players,
    MIN(rank) AS best_rank,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ranking_value) AS median_value,
    MAX(ranking_value) AS max_value
FROM neople.cyphers_character_ranking
GROUP BY character_id, ranking_type
ORDER BY ranking_type, median_value DESC NULLS LAST;

-- 7. Cyphers: character win rate within the automatically collected top-rating
-- player sample. This is not a whole-population estimate.
SELECT
    character_id,
    MAX(character_name) AS character_name,
    COUNT(*) AS matches,
    SUM(CASE WHEN LOWER(result) IN ('win', '승리', 'true') THEN 1 ELSE 0 END) AS wins,
    ROUND(
        100.0 * SUM(CASE WHEN LOWER(result) IN ('win', '승리', 'true') THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0), 2
    ) AS win_rate_pct,
    AVG(kill_count) AS avg_kills,
    AVG(assist_count) AS avg_assists
FROM neople.cyphers_player_match_performance
GROUP BY character_id
HAVING COUNT(*) >= 10
ORDER BY win_rate_pct DESC;

-- 8. Cyphers: character-item usage and performance within the same sample.
SELECT
    p.character_id,
    MAX(p.character_name) AS character_name,
    i.item_id,
    MAX(i.item_name) AS item_name,
    COUNT(DISTINCT p.match_id) AS matches,
    AVG(p.kill_count) AS avg_kills,
    AVG(p.assist_count) AS avg_assists,
    AVG(CASE WHEN LOWER(p.result) IN ('win', '승리', 'true') THEN 1.0 ELSE 0.0 END) * 100 AS win_rate_pct
FROM neople.cyphers_player_match_performance p
JOIN neople.cyphers_match_item i
  ON i.match_id = p.match_id
 AND i.character_id = p.character_id
GROUP BY p.character_id, i.item_id
HAVING COUNT(DISTINCT p.match_id) >= 10
ORDER BY p.character_id, win_rate_pct DESC;
