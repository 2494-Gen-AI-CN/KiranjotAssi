-- use case 5: price cut to value
-- Client question: What would a 20% price cut save for the same workload?
-- Decision: Estimate savings if a vendor offers a 20% cut at the same terms.
WITH battle_models AS (
  SELECT DISTINCT m.model_id
  FROM `desk-asthapatel25.llm_dw.fact_preference_battle` AS f
  CROSS JOIN UNNEST([f.model_a_key, f.model_b_key]) AS model_key
  JOIN `desk-asthapatel25.llm_dw.dim_model` AS m
    ON m.model_key = model_key
)
SELECT
  m.model_id,
  m.blended_price_per_m AS baseline_cost_per_m,
  m.blended_price_per_m * NUMERIC '0.80' AS scenario_cost_per_m,
  m.blended_price_per_m * NUMERIC '0.20' AS savings_per_m
FROM battle_models AS b
JOIN `desk-asthapatel25.llm_dw.dim_model` AS m USING (model_id)
WHERE m.is_current AND m.blended_price_per_m > 0
ORDER BY savings_per_m DESC;