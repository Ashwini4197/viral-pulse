-- =============================================================
--  VIRAL PULSE — Power BI Query Templates
--  Paste these into Power BI's "Native Query" mode
--  Connection: PostgreSQL DirectQuery
-- =============================================================


-- ---- PAGE 1: Sentiment Gauge (last 24 hours) ----

SELECT
    label,
    COUNT(*) AS count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS percentage
FROM sentiment_scores ss
JOIN raw_posts rp ON ss.post_id = rp.post_id
WHERE rp.created_utc >= NOW() - INTERVAL '24 hours'
GROUP BY label
ORDER BY count DESC;


-- ---- PAGE 1: Sentiment Trend Line (last 7 days, hourly) ----

SELECT
    hour_bucket,
    subreddit,
    avg_sentiment,
    positive_pct,
    negative_pct,
    total_posts
FROM vw_sentiment_by_hour
WHERE hour_bucket >= NOW() - INTERVAL '7 days'
ORDER BY hour_bucket;


-- ---- PAGE 2: Trending Keywords Timeline ----

SELECT
    subreddit,
    keyword,
    hour_bucket,
    frequency,
    spike_ratio,
    is_trending
FROM vw_trending_keywords
WHERE hour_bucket >= NOW() - INTERVAL '7 days'
ORDER BY hour_bucket DESC, spike_ratio DESC;


-- ---- PAGE 2: Top Keywords Right Now (last 6 hours) ----

SELECT
    subreddit,
    keyword,
    SUM(frequency) AS total_mentions,
    MAX(spike_ratio) AS peak_spike_ratio,
    BOOL_OR(is_trending) AS currently_trending
FROM vw_trending_keywords
WHERE hour_bucket >= NOW() - INTERVAL '6 hours'
GROUP BY subreddit, keyword
ORDER BY total_mentions DESC
LIMIT 30;


-- ---- PAGE 3: Entity Intelligence — Top Entities (last 7 days) ----

SELECT
    entity_text,
    entity_type,
    SUM(mention_count) AS total_mentions,
    ROUND(AVG(avg_sentiment)::NUMERIC, 3) AS avg_sentiment,
    COUNT(DISTINCT subreddit) AS subreddit_spread
FROM vw_entity_surge
WHERE day_bucket >= NOW() - INTERVAL '7 days'
GROUP BY entity_text, entity_type
ORDER BY total_mentions DESC
LIMIT 50;


-- ---- PAGE 4: Trend Alert Table ----

SELECT
    subreddit,
    keyword,
    MAX(frequency)          AS peak_hourly_frequency,
    MAX(rolling_avg_7d)     AS normal_avg,
    MAX(spike_ratio)        AS spike_ratio,
    MIN(hour_bucket)        AS first_detected
FROM vw_trending_keywords
WHERE is_trending = TRUE
  AND hour_bucket >= NOW() - INTERVAL '48 hours'
GROUP BY subreddit, keyword
ORDER BY spike_ratio DESC;
