-- 3. dim_language: filter by english
CREATE OR REPLACE TABLE `desk-asthapatel25.llm_dw.dim_language` AS
WITH languages AS(
  SELECT DISTINCT COALESCE(NULLIF(TRIM(language), ''),'und') AS language_code
  FROM `desk-asthapatel25.llm_staging.stg_battles`
)
SELECT 
  FARM_FINGERPRINT(language_code) AS language_key,
  language_code,
  language_code = 'en' AS is_english
FROM languages;