"""
viral_pulse/src/ingestion/reddit_collector.py

Pulls recent posts from target subreddits using PRAW.
Returns a list of dicts ready to insert into raw_posts.

Setup: https://www.reddit.com/prefs/apps → create a "script" app.
"""

import os
import logging
from datetime import datetime, timezone
from typing import List, Dict

import praw
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def get_reddit_client() -> praw.Reddit:
    return praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent=os.getenv("REDDIT_USER_AGENT", "ViralPulse/1.0"),
    )


def fetch_subreddit_posts(
    subreddit_name: str,
    limit: int = 100,
    sort: str = "new",          # 'new' | 'hot' | 'top'
) -> List[Dict]:
    """
    Fetch posts from a single subreddit.

    Args:
        subreddit_name: e.g. 'technology'
        limit:          max posts to pull (Reddit caps at 1000)
        sort:           listing type

    Returns:
        List of post dicts matching raw_posts schema.
    """
    reddit = get_reddit_client()
    subreddit = reddit.subreddit(subreddit_name)

    listing = {
        "new": subreddit.new,
        "hot": subreddit.hot,
        "top": subreddit.top,
    }.get(sort, subreddit.new)

    posts = []
    for submission in listing(limit=limit):
        posts.append({
            "post_id":      submission.id,
            "source":       "reddit",
            "subreddit":    subreddit_name,
            "title":        submission.title,
            "body":         submission.selftext[:2000] if submission.selftext else None,
            "author":       str(submission.author) if submission.author else "[deleted]",
            "url":          submission.url,
            "score":        submission.score,
            "num_comments": submission.num_comments,
            "created_utc":  datetime.fromtimestamp(
                                submission.created_utc, tz=timezone.utc
                            ),
        })

    logger.info(f"Fetched {len(posts)} posts from r/{subreddit_name}")
    return posts


def fetch_all_subreddits(limit_per: int = 100) -> List[Dict]:
    """
    Pull posts from all TARGET_SUBREDDITS defined in .env.
    """
    targets = os.getenv("TARGET_SUBREDDITS", "technology").split(",")
    all_posts = []

    for name in targets:
        name = name.strip()
        try:
            posts = fetch_subreddit_posts(name, limit=limit_per)
            all_posts.extend(posts)
        except Exception as e:
            logger.error(f"Failed to fetch r/{name}: {e}")

    logger.info(f"Total posts collected: {len(all_posts)}")
    return all_posts


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    posts = fetch_all_subreddits(limit_per=10)
    for p in posts[:3]:
        print(p["subreddit"], "|", p["title"][:80])
