-- =============================================================
--  VIRAL PULSE — Trending Keywords View
--  Flags any keyword with frequency > 2x its 7-day rolling avg
-- =============================================================

CREATE OR REPLACE VIEW vw_trending_keywords AS
WITH rolling_avg AS (
    SELECT
        subreddit,
        keyword,
        hour_bucket,
        frequency,
        AVG(frequency) OVER (
            PARTITION BY subreddit, keyword
            ORDER BY hour_bucket
            ROWS BETWEEN 168 PRECEDING AND 1 PRECEDING   -- 7 days of hourly data
        ) AS rolling_avg_7d,
        SUM(frequency) OVER (
            PARTITION BY subreddit, keyword
            ORDER BY hour_bucket
            ROWS BETWEEN 168 PRECEDING AND CURRENT ROW
        ) AS cumulative_total
    FROM keyword_trends
)
SELECT
    subreddit,
    keyword,
    hour_bucket,
    frequency,
    ROUND(rolling_avg_7d::NUMERIC, 2)                     AS rolling_avg_7d,
    ROUND((frequency / NULLIF(rolling_avg_7d, 0))::NUMERIC, 2) AS spike_ratio,
    CASE
        WHEN rolling_avg_7d IS NULL THEN FALSE             -- Not enough history yet
        WHEN frequency > (rolling_avg_7d * 2.0) THEN TRUE  -- Spiking!
        ELSE FALSE
    END AS is_trending
FROM rolling_avg
ORDER BY hour_bucket DESC, spike_ratio DESC NULLS LAST;


-- =============================================================
--  Quick sentiment summary view (used by Power BI Sentiment page)
-- =============================================================

CREATE OR REPLACE VIEW vw_sentiment_by_hour AS
SELECT
    DATE_TRUNC('hour', rp.created_utc)  AS hour_bucket,
    rp.subreddit,
    COUNT(*)                            AS total_posts,
    ROUND(AVG(ss.compound)::NUMERIC, 3) AS avg_sentiment,
    ROUND(
        100.0 * SUM(CASE WHEN ss.label = 'positive' THEN 1 ELSE 0 END) / COUNT(*),
        1
    ) AS positive_pct,
    ROUND(
        100.0 * SUM(CASE WHEN ss.label = 'negative' THEN 1 ELSE 0 END) / COUNT(*),
        1
    ) AS negative_pct,
    ROUND(
        100.0 * SUM(CASE WHEN ss.label = 'neutral'  THEN 1 ELSE 0 END) / COUNT(*),
        1
    ) AS neutral_pct
FROM raw_posts rp
JOIN sentiment_scores ss ON rp.post_id = ss.post_id
GROUP BY 1, 2
ORDER BY 1 DESC;


-- =============================================================
--  Entity surge view (used by Power BI Entity Map page)
-- =============================================================

CREATE OR REPLACE VIEW vw_entity_surge AS
SELECT
    ee.entity_text,
    ee.entity_type,
    rp.subreddit,
    DATE_TRUNC('day', rp.created_utc)  AS day_bucket,
    COUNT(*)                            AS mention_count,
    ROUND(AVG(ss.compound)::NUMERIC, 3) AS avg_sentiment
FROM extracted_entities ee
JOIN raw_posts rp         ON ee.post_id = rp.post_id
JOIN sentiment_scores ss  ON rp.post_id = ss.post_id
WHERE ee.entity_type IN ('ORG', 'PERSON', 'PRODUCT')
GROUP BY 1, 2, 3, 4
ORDER BY 4 DESC, 5 DESC;
