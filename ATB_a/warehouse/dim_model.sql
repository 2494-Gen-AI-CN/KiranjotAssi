-- 4. dim_model

-- Run in BigQuery Studio after the three staging tables are loaded.
-- The starter map uses exact identifiers. Maintain verified aliases in stg_model_map.
CREATE TABLE IF NOT EXISTS `desk-asthapatel25.llm_staging.stg_model_map` AS
WITH arena_models AS (
  SELECT model_a AS arena_name FROM `desk-asthapatel25.llm_staging.stg_battles`
  UNION DISTINCT
  SELECT model_b AS arena_name FROM `desk-asthapatel25.llm_staging.stg_battles`
),
leaderboard_models AS (
  SELECT DISTINCT model_name
  FROM `desk-asthapatel25.llm_staging.stg_leaderboard`
  WHERE category = 'overall' AND leaderboard_variant = 'text_style_control'
),
openrouter_models AS (
  SELECT DISTINCT model_id
  FROM `desk-asthapatel25.llm_staging.stg_openrouter`
)
SELECT
  a.arena_name AS model_id,
  a.arena_name,
  l.model_name AS leaderboard_name,
  p.model_id AS openrouter_id
FROM arena_models AS a
LEFT JOIN leaderboard_models AS l ON l.model_name = a.arena_name
LEFT JOIN openrouter_models AS p ON p.model_id = a.arena_name;

-- Use manual reference rates as fallbacks on current rows.
-- Their provenance stays in staging, and they do not create dated price events.
-- A version changes when the selected rating or observed price attributes change.
CREATE OR REPLACE TABLE `desk-asthapatel25.llm_dw.dim_model` AS
WITH arena_models AS (
  SELECT model_a AS arena_name FROM `desk-asthapatel25.llm_staging.stg_battles`
  UNION DISTINCT
  SELECT model_b AS arena_name FROM `desk-asthapatel25.llm_staging.stg_battles`
),
models AS (
  SELECT
    a.arena_name,
    COALESCE(m.model_id, a.arena_name) AS model_id,
    m.leaderboard_name,
    m.openrouter_id
  FROM arena_models AS a
  LEFT JOIN `desk-asthapatel25.llm_staging.stg_model_map` AS m USING (arena_name)
),
rating_events AS (
  SELECT
    m.arena_name,
    l.leaderboard_publish_date AS event_date,
    STRUCT(l.rating, l.rating_lower, l.rating_upper, l.organization, l.license) AS rating_state
  FROM models AS m
  JOIN `desk-asthapatel25.llm_staging.stg_leaderboard` AS l
    ON l.model_name = m.leaderboard_name
  WHERE l.category = 'overall' AND l.leaderboard_variant = 'text_style_control'
),
price_events AS (
  SELECT
    m.arena_name,
    p.snapshot_date AS event_date,
    STRUCT(p.prompt_usd_per_m, p.completion_usd_per_m, p.context_length) AS price_state
  FROM models AS m
  JOIN `desk-asthapatel25.llm_staging.stg_openrouter` AS p
    ON p.model_id = m.openrouter_id
  WHERE NOT p.is_free_variant AND NOT p.is_batch_variant
),
event_dates AS (
  SELECT arena_name, DATE '0001-01-01' AS event_date FROM models
  UNION DISTINCT
  SELECT arena_name, event_date FROM rating_events
  UNION DISTINCT
  SELECT arena_name, event_date FROM price_events
),
states AS (
  SELECT
    d.arena_name,
    d.event_date AS effective_from,
    LAST_VALUE(r.rating_state IGNORE NULLS) OVER history AS rating_state,
    LAST_VALUE(p.price_state IGNORE NULLS) OVER history AS price_state
  FROM event_dates AS d
  LEFT JOIN rating_events AS r USING (arena_name, event_date)
  LEFT JOIN price_events AS p USING (arena_name, event_date)
  WINDOW history AS (
    PARTITION BY d.arena_name ORDER BY d.event_date
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  )
),
state_signatures AS (
  SELECT *, TO_JSON_STRING(STRUCT(rating_state, price_state)) AS signature
  FROM states
),
changed_states AS (
  SELECT *
  FROM state_signatures
  QUALIFY signature IS DISTINCT FROM LAG(signature) OVER (
    PARTITION BY arena_name ORDER BY effective_from
  )
),
version_windows AS (
  SELECT
    *,
    LEAD(effective_from, 1, DATE '9999-12-31') OVER (
      PARTITION BY arena_name ORDER BY effective_from
    ) AS effective_to
  FROM changed_states
)
SELECT
  FARM_FINGERPRINT(TO_JSON_STRING(STRUCT(v.arena_name, v.effective_from))) AS model_key,
  m.model_id,
  v.arena_name,
  m.leaderboard_name,
  m.openrouter_id,
  v.rating_state.organization AS org,
  v.rating_state.license AS license_family,
  -- Project classification based on the Arena license labels present in the matched data.
  CASE
    WHEN LOWER(TRIM(v.rating_state.license)) = 'proprietary' THEN FALSE
    WHEN LOWER(TRIM(v.rating_state.license)) IN (
      'apache 2.0', 'mit', 'modified mit', 'gemma', 'llama', 'llama-3.3',
      'llama 4', 'cc-by-nc-4.0'
    ) THEN TRUE
    ELSE CAST(NULL AS BOOL)
  END AS is_open_weight,
  m.leaderboard_name IS NOT NULL AND m.openrouter_id IS NOT NULL AS is_mapped,
  v.rating_state.rating AS rating,
  v.rating_state.rating_lower AS rating_lower,
  v.rating_state.rating_upper AS rating_upper,
  COALESCE(v.price_state.prompt_usd_per_m, mp.prompt_usd_per_m) AS prompt_price_per_m,
  COALESCE(v.price_state.completion_usd_per_m, mp.completion_usd_per_m)
    AS completion_price_per_m,
  (
    COALESCE(v.price_state.prompt_usd_per_m, mp.prompt_usd_per_m)
    + COALESCE(v.price_state.completion_usd_per_m, mp.completion_usd_per_m)
  ) / NUMERIC '2'
    AS blended_price_per_m,
  v.price_state.context_length AS context_length,
  CAST(NULL AS BOOL) AS supports_tools,
  CAST(NULL AS BOOL) AS supports_image_input,
  v.effective_from,
  v.effective_to,
  v.effective_to = DATE '9999-12-31' AS is_current
FROM version_windows AS v
JOIN models AS m USING (arena_name)
LEFT JOIN `desk-asthapatel25.llm_staging.stg_manual_prices` AS mp
  ON mp.arena_name = v.arena_name AND v.effective_to = DATE '9999-12-31';

SELECT
  COUNT(*) AS model_versions,
  COUNTIF(is_current) AS current_models,
  COUNT(DISTINCT IF(leaderboard_name IS NOT NULL, arena_name, NULL)) AS leaderboard_matches,
  COUNT(DISTINCT IF(openrouter_id IS NOT NULL, arena_name, NULL)) AS openrouter_matches,
  COUNTIF(is_current AND blended_price_per_m IS NOT NULL) AS current_models_with_price,
  COUNTIF(is_current AND blended_price_per_m IS NULL) AS current_models_without_price
FROM `desk-asthapatel25.llm_dw.dim_model`;
