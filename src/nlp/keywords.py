"""
viral_pulse/src/nlp/keywords.py

TF-IDF keyword extraction per subreddit per hour.
Groups posts into hourly buckets, finds the top keywords,
and calculates their frequency for trend comparison.
"""

import re
import logging
from collections import Counter
from datetime import datetime
from typing import Dict, List

from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

logger = logging.getLogger(__name__)

# Extended stop words for social media / Reddit
CUSTOM_STOPWORDS = [
    "reddit", "post", "like", "just", "think", "know", "also",
    "would", "could", "really", "actually", "going", "thing", "people",
    "year", "years", "month", "week", "day", "time", "way", "said",
    "https", "http", "www", "com", "amp",
]


def extract_keywords_from_batch(
    posts: List[Dict],
    top_n: int = 20,
) -> List[Dict]:
    """
    Extract top TF-IDF keywords from a batch of posts.

    Groups posts by (subreddit, hour) bucket, then runs TF-IDF
    across all titles+bodies in that group.

    Returns:
        List of keyword_trends dicts ready to insert into DB.
    """
    if not posts:
        return []

    # Group posts by (subreddit, hour bucket)
    buckets: Dict[tuple, List[str]] = {}
    for post in posts:
        subreddit   = post.get("subreddit", "unknown")
        created_utc = post.get("created_utc", datetime.utcnow())

        # Truncate to hour
        hour_bucket = created_utc.replace(minute=0, second=0, microsecond=0)
        key = (subreddit, hour_bucket)

        title = post.get("title", "") or ""
        body  = post.get("body",  "") or ""
        text  = _clean_text(f"{title} {body}")

        buckets.setdefault(key, []).append(text)

    results = []
    for (subreddit, hour_bucket), texts in buckets.items():
        if len(texts) < 3:       # TF-IDF needs at least a few docs
            keywords = _frequency_fallback(texts, top_n)
        else:
            keywords = _tfidf_keywords(texts, top_n)

        for keyword, frequency, tfidf_score in keywords:
            results.append({
                "subreddit":   subreddit,
                "keyword":     keyword,
                "hour_bucket": hour_bucket,
                "frequency":   frequency,
                "tfidf_score": round(tfidf_score, 4),
                "is_trending": False,   # Updated later by SQL view / spike detector
            })

    logger.info(f"Extracted {len(results)} keyword records across {len(buckets)} buckets")
    return results


def _clean_text(text: str) -> str:
    """Lowercase, strip URLs and special chars."""
    text = text.lower()
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[^a-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _tfidf_keywords(texts: List[str], top_n: int) -> List[tuple]:
    """Run TF-IDF and return top N (keyword, frequency, score)."""
    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=500,
        ngram_range=(1, 2),        # Unigrams + bigrams
        token_pattern=r"\b[a-z]{3,}\b",  # Words of 3+ chars
    )
    # Add custom stopwords on top of sklearn's English list
    vectorizer.stop_words_ = (vectorizer.stop_words_ or set()) | set(CUSTOM_STOPWORDS)

    try:
        matrix = vectorizer.fit_transform(texts)
    except ValueError:
        return []

    feature_names = vectorizer.get_feature_names_out()
    mean_scores   = np.asarray(matrix.mean(axis=0)).flatten()
    top_indices   = mean_scores.argsort()[::-1][:top_n]

    # Count raw frequency too (for trend comparison)
    all_words = " ".join(texts).split()
    word_freq = Counter(all_words)

    results = []
    for idx in top_indices:
        keyword = feature_names[idx]
        score   = float(mean_scores[idx])
        freq    = sum(word_freq.get(w, 0) for w in keyword.split())
        results.append((keyword, freq, score))

    return results


def _frequency_fallback(texts: List[str], top_n: int) -> List[tuple]:
    """For small batches: simple word frequency, no TF-IDF."""
    all_words = " ".join(texts).split()
    counts    = Counter(
        w for w in all_words
        if len(w) >= 3 and w not in CUSTOM_STOPWORDS
    )
    return [(word, count, float(count)) for word, count in counts.most_common(top_n)]


if __name__ == "__main__":
    from datetime import timezone
    sample_posts = [
        {"subreddit": "technology", "title": "OpenAI releases new AI model", "body": "GPT is impressive", "created_utc": datetime.now(timezone.utc)},
        {"subreddit": "technology", "title": "AI regulation debate heats up", "body": "Government wants to regulate artificial intelligence models", "created_utc": datetime.now(timezone.utc)},
        {"subreddit": "technology", "title": "Machine learning benchmark results", "body": "New AI model beats GPT on reasoning tasks", "created_utc": datetime.now(timezone.utc)},
    ]
    keywords = extract_keywords_from_batch(sample_posts)
    for kw in keywords[:5]:
        print(kw)
