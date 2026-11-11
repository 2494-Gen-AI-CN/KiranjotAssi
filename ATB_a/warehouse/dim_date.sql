-- 1. dim_date dimension by pulling the dates from the source dataset
CREATE OR REPLACE TABLE `desk-asthapatel25.llm_dw.dim_date` AS 
WITH battle_dates AS(
  SELECT DISTINCT DATE(timestamp,'UTC') AS full_date
  FROM `desk-asthapatel25.llm_staging.stg_battles`
)
SELECT 
  CAST(FORMAT_DATE('%Y%m%d', full_date) AS INT64) AS date_key,
  full_date,
  EXTRACT(YEAR FROM full_date) AS year,
  EXTRACT(MONTH FROM full_date) AS month,
  FORMAT_DATE('%B', full_date) AS month_name,
  EXTRACT(DAYOFWEEK FROM full_date) AS day_of_week
FROM battle_dates;