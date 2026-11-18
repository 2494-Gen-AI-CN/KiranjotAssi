-- use case 3: larger model vs. longer context pay off
-- Client question: Which models hold their rank after style adjustment?
-- Decision: Identify models to shortlist for the client's own task evaluations.
WITH battle_models AS (
  SELECT m.leaderboard_name, COUNT(*) AS model_appearances
  FROM `desk-asthapatel25.llm_dw.fact_preference_battle` AS f
  CROSS JOIN UNNEST([f.model_a_key, f.model_b_key]) AS model_key
  JOIN `desk-asthapatel25.llm_dw.dim_model` AS m
    ON m.model_key = model_key
  WHERE m.leaderboard_name IS NOT NULL
  GROUP BY m.leaderboard_name
),
paired AS (
  SELECT
    l.leaderboard_publish_date AS snapshot_date,
    l.model_name,
    b.model_appearances,
    MAX(IF(l.leaderboard_variant = 'text', l.rank, NULL)) AS published_raw_rank,
    MAX(IF(l.leaderboard_variant = 'text_style_control', l.rank, NULL))
      AS published_style_rank
  FROM `desk-asthapatel25.llm_staging.stg_leaderboard` AS l
  JOIN battle_models AS b ON l.model_name = b.leaderboard_name
  WHERE l.category = 'overall'
    AND l.leaderboard_publish_date BETWEEN DATE '2025-04-17' AND DATE '2025-07-24'
  GROUP BY l.leaderboard_publish_date, l.model_name, b.model_appearances
  HAVING published_raw_rank IS NOT NULL AND published_style_rank IS NOT NULL
),
chosen_date AS (
  SELECT snapshot_date
  FROM paired
  GROUP BY snapshot_date
  ORDER BY COUNT(*) DESC, snapshot_date DESC
  LIMIT 1
),
reranked AS (
  SELECT
    snapshot_date,
    model_name,
    model_appearances,
    RANK() OVER (ORDER BY published_raw_rank) AS raw_rank,
    RANK() OVER (ORDER BY published_style_rank) AS style_controlled_rank
  FROM paired
  JOIN chosen_date USING (snapshot_date)
)
SELECT
  *,
  style_controlled_rank - raw_rank AS style_rank_shift
FROM reranked
ORDER BY ABS(style_rank_shift) DESC, raw_rank;