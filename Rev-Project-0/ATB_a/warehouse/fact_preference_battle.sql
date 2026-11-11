-- 5. fact table
-- Run after dim_date, dim_language, dim_task, and dim_model exist.
-- Grain: one row per accepted Arena vote.
CREATE OR REPLACE TABLE `desk-asthapatel25.llm_dw.fact_preference_battle` AS
WITH classified_battles AS (
  SELECT
    b.*,
    DATE(b.timestamp, 'UTC') AS battle_date,
    COALESCE(NULLIF(TRIM(b.language), ''), 'und') AS language_code,
    CASE
      WHEN b.is_code THEN 'coding'
      WHEN JSON_VALUE(b.category_tag_json, '$."math_v0.1".math') = 'true'
        THEN 'math'
      WHEN JSON_VALUE(b.category_tag_json, '$."creative_writing_v0.1".creative_writing') = 'true'
        THEN 'creative_writing'
      WHEN JSON_VALUE(b.category_tag_json, '$."if_v0.1".if') = 'true'
        THEN 'instruction_following'
      ELSE 'general'
    END AS task_name
  FROM `desk-asthapatel25.llm_staging.stg_battles` AS b
),
dated_prices AS (
  SELECT
    model_id,
    snapshot_date AS effective_from,
    LEAD(snapshot_date, 1, DATE '9999-12-31') OVER (
      PARTITION BY model_id ORDER BY snapshot_date
    ) AS effective_to,
    completion_usd_per_m
  FROM `desk-asthapatel25.llm_staging.stg_openrouter`
  WHERE NOT is_free_variant AND NOT is_batch_variant
)
SELECT
  b.id AS battle_id,
  b.timestamp AS battle_ts,
  d.date_key,
  a.model_key AS model_a_key,
  opponent.model_key AS model_b_key,
  l.language_key,
  t.task_key,
  b.winner,
  CASE b.winner
    WHEN 'model_a' THEN 1.0
    WHEN 'model_b' THEN 0.0
    WHEN 'tie' THEN 0.5
    ELSE NULL
  END AS score_a,
  CAST(NULL AS INT64) AS prompt_chars,
  b.answer_tokens_a,
  b.answer_tokens_b,
  b.answer_tokens_a - b.answer_tokens_b AS len_diff,
  b.is_code,
  -- Use dated OpenRouter rates. Manual fallback rates have no battle-date validity.
  b.answer_tokens_a * price_a.completion_usd_per_m / NUMERIC '1000000' AS est_cost_usd_a,
  b.answer_tokens_b * price_b.completion_usd_per_m / NUMERIC '1000000' AS est_cost_usd_b,
  '140k' AS release,
  b.run_id,
  b.header_count_a,
  b.list_count_a,
  b.bold_count_a,
  b.header_count_b,
  b.list_count_b,
  b.bold_count_b
FROM classified_battles AS b
LEFT JOIN `desk-asthapatel25.llm_dw.dim_date` AS d
  ON d.full_date = b.battle_date
LEFT JOIN `desk-asthapatel25.llm_dw.dim_language` AS l
  ON l.language_code = b.language_code
LEFT JOIN `desk-asthapatel25.llm_dw.dim_task` AS t
  ON t.task_name = b.task_name
LEFT JOIN `desk-asthapatel25.llm_dw.dim_model` AS a
  ON a.arena_name = b.model_a
  AND b.battle_date >= a.effective_from AND b.battle_date < a.effective_to
LEFT JOIN `desk-asthapatel25.llm_dw.dim_model` AS opponent
  ON opponent.arena_name = b.model_b
  AND b.battle_date >= opponent.effective_from AND b.battle_date < opponent.effective_to
LEFT JOIN dated_prices AS price_a
  ON a.openrouter_id = price_a.model_id
  AND b.battle_date >= price_a.effective_from AND b.battle_date < price_a.effective_to
LEFT JOIN dated_prices AS price_b
  ON opponent.openrouter_id = price_b.model_id
  AND b.battle_date >= price_b.effective_from AND b.battle_date < price_b.effective_to;

SELECT
  COUNT(*) AS fact_rows,
  COUNT(DISTINCT battle_id) AS distinct_battle_ids,
  COUNTIF(est_cost_usd_a IS NOT NULL OR est_cost_usd_b IS NOT NULL) AS votes_with_dated_cost
FROM `desk-asthapatel25.llm_dw.fact_preference_battle`;
