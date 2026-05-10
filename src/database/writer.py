"""
viral_pulse/src/database/writer.py

Batch insert helpers for all four tables.
Uses INSERT ... ON CONFLICT DO NOTHING to handle duplicates
(safe to re-run the pipeline without creating duplicate rows).
"""

import logging
from typing import List, Dict

from sqlalchemy import text
from src.database.connection import engine

logger = logging.getLogger(__name__)


def insert_raw_posts(posts: List[Dict]) -> int:
    """
    Insert posts into raw_posts. Skips duplicates by post_id.
    Returns count of newly inserted rows.
    """
    if not posts:
        return 0

    sql = text("""
        INSERT INTO raw_posts
            (post_id, source, subreddit, title, body, author, url,
             score, num_comments, created_utc)
        VALUES
            (:post_id, :source, :subreddit, :title, :body, :author, :url,
             :score, :num_comments, :created_utc)
        ON CONFLICT (post_id) DO NOTHING
    """)

    with engine.begin() as conn:
        result = conn.execute(sql, posts)

    inserted = result.rowcount
    logger.info(f"raw_posts: inserted {inserted}/{len(posts)}")
    return inserted


def insert_sentiment_scores(scores: List[Dict]) -> int:
    """
    Insert sentiment scores. One row per post.
    'scores' should be a list of dicts with keys:
        post_id, compound, positive, negative, neutral, label
    """
    if not scores:
        return 0

    sql = text("""
        INSERT INTO sentiment_scores
            (post_id, compound, positive, negative, neutral, label)
        VALUES
            (:post_id, :compound, :positive, :negative, :neutral, :label)
        ON CONFLICT DO NOTHING
    """)

    with engine.begin() as conn:
        result = conn.execute(sql, scores)

    inserted = result.rowcount
    logger.info(f"sentiment_scores: inserted {inserted}/{len(scores)}")
    return inserted


def insert_entities(entities: List[Dict]) -> int:
    """
    Insert extracted entities.
    'entities' list of dicts: post_id, entity_text, entity_type, mention_count
    """
    if not entities:
        return 0

    sql = text("""
        INSERT INTO extracted_entities
            (post_id, entity_text, entity_type, mention_count)
        VALUES
            (:post_id, :entity_text, :entity_type, :mention_count)
        ON CONFLICT DO NOTHING
    """)

    with engine.begin() as conn:
        result = conn.execute(sql, entities)

    inserted = result.rowcount
    logger.info(f"extracted_entities: inserted {inserted}/{len(entities)}")
    return inserted


def insert_keyword_trends(keywords: List[Dict]) -> int:
    """
    Insert keyword trend records.
    """
    if not keywords:
        return 0

    sql = text("""
        INSERT INTO keyword_trends
            (subreddit, keyword, hour_bucket, frequency, tfidf_score, is_trending)
        VALUES
            (:subreddit, :keyword, :hour_bucket, :frequency, :tfidf_score, :is_trending)
        ON CONFLICT DO NOTHING
    """)

    with engine.begin() as conn:
        result = conn.execute(sql, keywords)

    inserted = result.rowcount
    logger.info(f"keyword_trends: inserted {inserted}/{len(keywords)}")
    return inserted


def refresh_daily_summary() -> None:
    """
    Upsert today's daily_summary row from live data.
    Call this at end of each pipeline run.
    """
    sql = text("""
        INSERT INTO daily_summary
            (summary_date, subreddit, total_posts, avg_sentiment,
             positive_pct, negative_pct, neutral_pct)
        SELECT
            DATE(rp.created_utc)  AS summary_date,
            rp.subreddit,
            COUNT(*)              AS total_posts,
            AVG(ss.compound)      AS avg_sentiment,
            ROUND(100.0 * SUM(CASE WHEN ss.label='positive' THEN 1 ELSE 0 END)/COUNT(*), 1),
            ROUND(100.0 * SUM(CASE WHEN ss.label='negative' THEN 1 ELSE 0 END)/COUNT(*), 1),
            ROUND(100.0 * SUM(CASE WHEN ss.label='neutral'  THEN 1 ELSE 0 END)/COUNT(*), 1)
        FROM raw_posts rp
        JOIN sentiment_scores ss ON rp.post_id = ss.post_id
        WHERE DATE(rp.created_utc) = CURRENT_DATE
        GROUP BY 1, 2
        ON CONFLICT (summary_date, subreddit)
        DO UPDATE SET
            total_posts   = EXCLUDED.total_posts,
            avg_sentiment = EXCLUDED.avg_sentiment,
            positive_pct  = EXCLUDED.positive_pct,
            negative_pct  = EXCLUDED.negative_pct,
            neutral_pct   = EXCLUDED.neutral_pct
    """)

    with engine.begin() as conn:
        conn.execute(sql)

    logger.info("daily_summary: refreshed for today")
