-- Compare SCD2 ratings on dates with leaderboard observations for all 3 models.
-- Uses the same overall, style-controlled leaderboard as dim_model.
WITH selected_models AS (
  SELECT DISTINCT model_id, leaderboard_name
  FROM `desk-asthapatel25.llm_dw.dim_model`
  WHERE model_id IN ('gemini-2.5-pro', 'deepseek-r1-0528', 'o3-2025-04-16')
),
shared_dates AS (
  SELECT l.leaderboard_publish_date AS snapshot_date
  FROM `desk-asthapatel25.llm_staging.stg_leaderboard` AS l
  JOIN selected_models AS m ON l.model_name = m.leaderboard_name
  WHERE l.category = 'overall'
    AND l.leaderboard_variant = 'text_style_control'
    AND l.rating IS NOT NULL
  GROUP BY snapshot_date
  HAVING COUNT(DISTINCT m.model_id) = 3
),
history AS (
  SELECT
    s.snapshot_date,
    d.model_id,
    d.rating,
    d.rating_lower,
    d.rating_upper
  FROM shared_dates AS s
  JOIN `desk-asthapatel25.llm_dw.dim_model` AS d
    ON s.snapshot_date >= d.effective_from
    AND s.snapshot_date < d.effective_to
  WHERE d.model_id IN ('gemini-2.5-pro', 'deepseek-r1-0528', 'o3-2025-04-16')
    AND d.rating IS NOT NULL
)
SELECT
  *,
  rating - FIRST_VALUE(rating) OVER (
    PARTITION BY model_id ORDER BY snapshot_date
  ) AS change_since_start
FROM history
ORDER BY snapshot_date, model_id;
