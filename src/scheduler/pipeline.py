"""
viral_pulse/src/scheduler/pipeline.py

Main orchestrator. Runs the full pipeline on a schedule:
  1. Fetch posts from Reddit
  2. Score sentiment with VADER
  3. Extract named entities with spaCy
  4. Extract keywords with TF-IDF
  5. Write everything to PostgreSQL
  6. Refresh daily summary

Run: python src/scheduler/pipeline.py
"""

import os
import logging
import sys
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv

# Make sure src/ is on the path when running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.ingestion.reddit_collector import fetch_all_subreddits
from src.nlp.sentiment import score_posts
from src.nlp.entities import extract_from_post
from src.nlp.keywords import extract_keywords_from_batch
from src.database.writer import (
    insert_raw_posts,
    insert_sentiment_scores,
    insert_entities,
    insert_keyword_trends,
    refresh_daily_summary,
)

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("pipeline")


def run_pipeline() -> None:
    """Full pipeline run — called by the scheduler every N minutes."""
    start = datetime.utcnow()
    logger.info("=" * 60)
    logger.info(f"Pipeline started at {start.isoformat()}Z")

    # ── Step 1: Ingest ────────────────────────────────────────────
    limit = int(os.getenv("POSTS_PER_SUBREDDIT", 100))
    posts = fetch_all_subreddits(limit_per=limit)

    if not posts:
        logger.warning("No posts fetched — skipping this run.")
        return

    # ── Step 2: Save raw posts ────────────────────────────────────
    insert_raw_posts(posts)

    # ── Step 3: Sentiment ─────────────────────────────────────────
    scored_posts = score_posts(posts)

    sentiment_records = [
        {
            "post_id":  p["post_id"],
            **p["sentiment"],
        }
        for p in scored_posts
    ]
    insert_sentiment_scores(sentiment_records)

    # ── Step 4: Named entities ────────────────────────────────────
    all_entities = []
    for post in posts:
        all_entities.extend(extract_from_post(post))
    insert_entities(all_entities)

    # ── Step 5: Keywords ──────────────────────────────────────────
    keyword_records = extract_keywords_from_batch(posts)
    insert_keyword_trends(keyword_records)

    # ── Step 6: Refresh summary ───────────────────────────────────
    refresh_daily_summary()

    elapsed = (datetime.utcnow() - start).total_seconds()
    logger.info(f"Pipeline complete in {elapsed:.1f}s — {len(posts)} posts processed")
    logger.info("=" * 60)


def main():
    interval_minutes = int(os.getenv("SCHEDULE_INTERVAL_MINUTES", 60))

    logger.info(f"🚀 Viral Pulse pipeline starting — interval: {interval_minutes} min")

    # Run immediately on startup
    run_pipeline()

    # Then schedule
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(
        run_pipeline,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="viral_pulse_pipeline",
        name="Viral Pulse hourly pipeline",
        misfire_grace_time=300,  # 5-minute grace if server is briefly down
    )

    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Pipeline stopped by user.")
        scheduler.shutdown()


if __name__ == "__main__":
    main()
