-- 2. dim_task: unique categories of tasks
CREATE OR REPLACE TABLE `desk-asthapatel25.llm_dw.dim_task` AS 
SELECT 1 AS task_key, 'coding' AS task_name
UNION ALL SELECT 2, 'math'
UNION ALL SELECT 3, 'creative_writing'
UNION ALL SELECT 4, 'instruction_following'
UNION ALL SELECT 5, 'general';