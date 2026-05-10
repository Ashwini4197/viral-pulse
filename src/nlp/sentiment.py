"""
viral_pulse/src/nlp/sentiment.py

VADER sentiment scoring for Reddit posts.
VADER is purpose-built for social media text — handles slang,
caps, punctuation, and emoticons without needing training data.

Returns: compound score (-1 to +1) + positive/negative/neutral ratios + label.
"""

from typing import Dict, List
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()


def score_text(text: str) -> Dict:
    """
    Score a single piece of text.

    Args:
        text: Post title + body combined (recommended) or title alone.

    Returns:
        {
          'compound':  float,   # -1.0 to +1.0
          'positive':  float,   # proportion of positive sentiment
          'negative':  float,
          'neutral':   float,
          'label':     str      # 'positive' | 'negative' | 'neutral'
        }
    """
    if not text or not text.strip():
        return {
            "compound": 0.0,
            "positive": 0.0,
            "negative": 0.0,
            "neutral":  1.0,
            "label":    "neutral",
        }

    scores = _analyzer.polarity_scores(text)

    # Standard VADER thresholds: >=0.05 positive, <=-0.05 negative
    compound = scores["compound"]
    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"

    return {
        "compound": round(compound, 4),
        "positive": round(scores["pos"], 4),
        "negative": round(scores["neg"], 4),
        "neutral":  round(scores["neu"], 4),
        "label":    label,
    }


def score_post(post: Dict) -> Dict:
    """
    Score a post dict from reddit_collector. Combines title + body.

    Returns the original post dict plus a 'sentiment' key.
    """
    title = post.get("title", "") or ""
    body  = post.get("body", "")  or ""
    combined = f"{title}. {body}".strip()

    return {**post, "sentiment": score_text(combined)}


def score_posts(posts: List[Dict]) -> List[Dict]:
    """Score a batch of post dicts."""
    return [score_post(p) for p in posts]


if __name__ == "__main__":
    samples = [
        "This is absolutely amazing and I love it so much!",
        "Terrible news. Everything is falling apart and I'm furious.",
        "New update released for the platform.",
    ]
    for s in samples:
        result = score_text(s)
        print(f"[{result['label']:8s}] {result['compound']:+.3f}  {s[:60]}")
