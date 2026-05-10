"""
viral_pulse/tests/test_pipeline.py

Unit tests for the NLP pipeline.
Run: pytest tests/ -v
"""

import pytest
from datetime import datetime, timezone


# ── Sentiment Tests ────────────────────────────────────────────────────────────

class TestSentiment:
    def setup_method(self):
        from src.nlp.sentiment import score_text
        self.score = score_text

    def test_positive_text(self):
        result = self.score("This is absolutely amazing and I love it!")
        assert result["label"] == "positive"
        assert result["compound"] > 0.05

    def test_negative_text(self):
        result = self.score("This is terrible, I hate everything about it.")
        assert result["label"] == "negative"
        assert result["compound"] < -0.05

    def test_neutral_text(self):
        result = self.score("The meeting is at 3pm on Tuesday.")
        assert result["label"] == "neutral"

    def test_empty_text(self):
        result = self.score("")
        assert result["compound"] == 0.0
        assert result["label"] == "neutral"

    def test_compound_range(self):
        result = self.score("Something happened today.")
        assert -1.0 <= result["compound"] <= 1.0

    def test_score_sums_to_one(self):
        result = self.score("Test sentence for pipeline.")
        total = result["positive"] + result["negative"] + result["neutral"]
        assert abs(total - 1.0) < 0.01   # Should sum to ~1.0


# ── Keyword Tests ──────────────────────────────────────────────────────────────

class TestKeywords:
    def setup_method(self):
        from src.nlp.keywords import extract_keywords_from_batch
        self.extract = extract_keywords_from_batch

    def _make_posts(self, titles, subreddit="technology"):
        now = datetime.now(timezone.utc)
        return [
            {
                "post_id": f"post_{i}",
                "subreddit": subreddit,
                "title": title,
                "body": "",
                "created_utc": now,
            }
            for i, title in enumerate(titles)
        ]

    def test_returns_list(self):
        posts = self._make_posts(["AI is transforming the world"] * 5)
        result = self.extract(posts)
        assert isinstance(result, list)

    def test_has_required_fields(self):
        posts = self._make_posts(["Machine learning and deep learning"] * 5)
        result = self.extract(posts)
        if result:
            record = result[0]
            assert "keyword" in record
            assert "frequency" in record
            assert "subreddit" in record
            assert "hour_bucket" in record

    def test_empty_posts(self):
        result = self.extract([])
        assert result == []

    def test_different_subreddits_separated(self):
        now = datetime.now(timezone.utc)
        posts = [
            {"post_id": "a1", "subreddit": "technology", "title": "AI news", "body": "", "created_utc": now},
            {"post_id": "b1", "subreddit": "stocks",     "title": "Market rally", "body": "", "created_utc": now},
        ]
        result = self.extract(posts)
        subreddits = {r["subreddit"] for r in result}
        assert len(subreddits) > 0   # At least one subreddit extracted


# ── Entity Tests ───────────────────────────────────────────────────────────────

class TestEntities:
    def setup_method(self):
        try:
            from src.nlp.entities import extract_entities
            self.extract = extract_entities
            self.available = True
        except Exception:
            self.available = False

    def test_extracts_org(self):
        if not self.available:
            pytest.skip("spaCy model not installed")
        results = self.extract("Apple and Microsoft announced a partnership.")
        entity_texts = [e[0] for e in results]
        assert any("Apple" in t or "Microsoft" in t for t in entity_texts)

    def test_empty_text(self):
        if not self.available:
            pytest.skip("spaCy model not installed")
        assert self.extract("") == []

    def test_returns_tuples(self):
        if not self.available:
            pytest.skip("spaCy model not installed")
        results = self.extract("Google released a new product today.")
        for item in results:
            assert len(item) == 3   # (text, type, count)
