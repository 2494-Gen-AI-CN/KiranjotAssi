-- Client question: Which Arena models offer the best chat preference for their price?
-- Decision: Shortlist models using recorded OpenRouter and manual prices.
-- The rates come from multiple sources and dates.
WITH appearances AS (
  SELECT model_a_key AS model_key, score_a AS score
  FROM `desk-asthapatel25.llm_dw.fact_preference_battle`
  UNION ALL
  SELECT model_b_key, 1.0 - score_a
  FROM `desk-asthapatel25.llm_dw.fact_preference_battle`
),
scores AS (
  SELECT
    m.arena_name AS model_id,
    AVG(CAST(a.score AS NUMERIC)) AS strength,
    COUNT(a.score) AS scored_battles
  FROM appearances AS a
  JOIN `desk-asthapatel25.llm_dw.dim_model` AS m USING (model_key)
  GROUP BY m.arena_name
),
all_models AS (
  SELECT
    s.*,
    m.openrouter_id,
    m.blended_price_per_m AS price
  FROM scores AS s
  LEFT JOIN `desk-asthapatel25.llm_dw.dim_model` AS m
    ON s.model_id = m.arena_name AND m.is_current
),
frontier AS (
  SELECT
    model_id,
    strength = MAX(strength) OVER (ORDER BY price)
      AND price = MIN(price) OVER (PARTITION BY strength) AS is_pareto_frontier
  FROM all_models
  WHERE price > 0 AND scored_battles >= 100
)
SELECT a.*, f.is_pareto_frontier
FROM all_models AS a
LEFT JOIN frontier AS f USING (model_id)
ORDER BY strength DESC, model_id;